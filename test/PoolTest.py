from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3
import json
import requests
import os
import time
import datetime as dt

def get_abi(contract_address: str):
    """
        Get contract abi from ABIs folder if exists, else download from etherscan API
    """
    contract_address = contract_address.lower()
    if not 'ABIs' in os.listdir():
        os.mkdir('ABIs')
    if contract_address + '.json' in os.listdir('ABIs'):
        return json.load(open('ABIs/'+contract_address+'.json'))
    abi = json.loads(requests.get('https://api.etherscan.io/api?module=contract&action=getabi&address={}'.format(contract_address.lower())).json()['result'])
    json.dump(abi, open('ABIs/'+contract_address + '.json', 'w'))
    return abi

def deploy_contract(contract_json, mine=True, **kwargs):
    contract = w3.eth.contract(abi=contract_json['abi'], bytecode=contract_json['bytecode'])
    construct_txn = contract.constructor(**kwargs).buildTransaction({
        'from': ETH_ACCOUNT_FROM.address,
        'nonce': w3.eth.getTransactionCount(ETH_ACCOUNT_FROM.address),
        'gas': 30*10**6,
        'gasPrice': int(w3.eth.gasPrice*1.15)})

    signed = ETH_ACCOUNT_FROM.signTransaction(construct_txn)
    hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    if mine:
        tx = w3.eth.wait_for_transaction_receipt(hash.hex())
        address = tx.contractAddress
        contract = w3.eth.contract(address, abi=contract_json['abi'])
        return contract
    return hash

def build_tx(func, mine=True):
    construct_txn = func.buildTransaction({
        'from': ETH_ACCOUNT_FROM.address,
        'nonce': w3.eth.getTransactionCount(ETH_ACCOUNT_FROM.address),
        'gas': 5*10**6,
        'gasPrice': int(w3.eth.gasPrice*1.15)})

    signed = ETH_ACCOUNT_FROM.signTransaction(construct_txn)
    hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    if mine:
        w3.provider.make_request('evm_mine', {})
        tx = w3.eth.wait_for_transaction_receipt(hash.hex())
        return tx
    return hash

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
ETH_ACCOUNT_FROM: LocalAccount = Account.from_key("0xdf57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656e")
ETH_ACCOUNT_ATTACKER: LocalAccount = Account.from_key("0xde9be858da4a475276426320d5e9262ecfc3ba460bfac56360bfa6c4c28b4ee0")
ETH_ACCOUNT_TARGET: LocalAccount = Account.from_key("0x689af8efa8c651a91ad287602527f3af2fe9f6501a7ac4b061667b5a93e037fd")

pair_json = json.load(open('../artifacts/contracts/UniswapV2Pair.sol/UniswapV2Pair.json'))
token_json = json.load(open('../artifacts/contracts/UniswapV2ERC20.sol/MyToken.json'))
# factory_json = json.load(open('../artifacts/contracts/UniswapV2Factory.sol/UniswapV2Factory.json'))
# router_json = json.load(open('../artifacts/contracts/UniswapV2Router02.sol/UniswapV2Router02.json'))
# pair_json = json.load(open('../node_modules/@uniswap/v2-core/build/UniswapV2Pair.json'))
# token_json = json.load(open('../node_modules/@uniswap/v2-core/build/MyToken.json'))
factory_json = json.load(open('../node_modules/@uniswap/v2-core/build/UniswapV2Factory.json'))
router_json = json.load(open('../node_modules/@uniswap/v2-periphery/build/UniswapV2Router02.json'))

#  Deploy factory
contract_factory = deploy_contract(factory_json, _feeToSetter=ETH_ACCOUNT_FROM.address)

#  Deploy token
contract_token_base = deploy_contract(token_json)
contract_token_quote = deploy_contract(token_json)
print('Deployed tokens address: ', contract_token_base.address, contract_token_quote.address)

#  Deploy pair
contract_pair = build_tx(contract_factory.functions.createPair(contract_token_base.address, contract_token_quote.address))
contract_pair = w3.eth.contract(w3.toChecksumAddress('0x'+contract_pair.logs[0]['data'][26:66]),
                                abi=pair_json['abi'])

#  Initialize pair
# tx = build_tx(contract_pair.functions.initialize(contract_token_base.address, contract_token_quote.address))
print('Deployed pool address: ', contract_pair.address)

#  Deploy the router contract
contract_router = deploy_contract(router_json, _factory=contract_factory.address, _WETH=contract_token_base.address)

#  Approve router for tokens
approve_base = build_tx(contract_token_base.functions.approve(contract_router.address, 50*10**18))
approve_quote = build_tx(contract_token_quote.functions.approve(contract_router.address, 50*10**18))

#  Add liquidity
tx = build_tx(contract_router.functions.addLiquidity(contract_token_base.address,
                                                     contract_token_quote.address,
                                                     10 * 10 ** 18,
                                                     10 * 10 ** 18,
                                                     10 * 10 ** 17,
                                                     10 * 10 ** 17,
                                                     # contract_pair.address,
                                                     ETH_ACCOUNT_FROM.address,
                                                     int((dt.datetime.now()+dt.timedelta(hours=1)).timestamp())))

#  Test simple swap
print('Base token amount before swap: ', contract_token_base.functions.balanceOf(ETH_ACCOUNT_FROM.address).call()/10**18)
print('Quote token amount before swap: ', contract_token_quote.functions.balanceOf(ETH_ACCOUNT_FROM.address).call()/10**18)
tx = build_tx(contract_router.functions.swapTokensForExactTokens(10**18,
                                                                 3*10**18,
                                                                 [contract_token_base.address, contract_token_quote.address],
                                                                 ETH_ACCOUNT_FROM.address,
                                                                 int((dt.datetime.now()+dt.timedelta(hours=1)).timestamp())),
              mine=True)
print('Base token amount after swap: ', contract_token_base.functions.balanceOf(ETH_ACCOUNT_FROM.address).call()/10**18)
print('Quote token amount after swap: ', contract_token_quote.functions.balanceOf(ETH_ACCOUNT_FROM.address).call()/10**18)