from eth_account.account import Account
from eth_account.signers.local import LocalAccount
from web3 import Web3
import json
import requests
import os
import time
import datetime as dt
from testing_optimizer import *

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
        w3.provider.make_request('evm_mine', {})
        tx = w3.eth.wait_for_transaction_receipt(hash.hex())
        address = tx.contractAddress
        contract = w3.eth.contract(address, abi=contract_json['abi'])
        return contract
    return hash

def build_tx(func, account, mine=True, nonce=None):
    construct_txn = func.buildTransaction({
        'from': account.address,
        'nonce': nonce if nonce else w3.eth.getTransactionCount(account.address),
        'gas': 20*10**6,
        'gasPrice': int(w3.eth.gasPrice*1.15)})

    signed = account.signTransaction(construct_txn)
    hash = w3.eth.sendRawTransaction(signed.rawTransaction)
    if mine:
        w3.provider.make_request('evm_mine', {})
        tx = w3.eth.wait_for_transaction_receipt(hash.hex())
        return tx
    return hash

def build_swap_router(contract_router, buy, amountIn, amountOutMin, account, mine=True):
    #  Test simple swap
    if buy:
        path = [contract_token_base.address, contract_token_quote.address]
    else:
        path = [contract_token_quote.address, contract_token_base.address]
    tx = build_tx(contract_router.functions.swapExactTokensForTokens(amountIn,
                                                                     amountOutMin,
                                                                     path,
                                                                     account.address,
                                                                     int((dt.datetime.now() + dt.timedelta(
                                                                         days=1)).timestamp())),
                  account,
                  mine)
    return tx

def build_swap_pair(contract_pair, buy, amountIn, amountOut, account, nonce, mine=True):
    if buy:
        amount1Out = amountOut
        amount0Out = 0
        build_tx(contract_token_base.functions.transfer(contract_pair.address, amountIn),
                 account,
                 mine=False,
                 nonce=nonce)

    else:
        amount0Out = amountOut
        amount1Out = 0
        build_tx(contract_token_quote.functions.transfer(contract_pair.address, amountIn),
                 account,
                 mine=False,
                 nonce=nonce)

    tx = build_tx(contract_pair.functions.swap(amount0Out,
                                               amount1Out,
                                               account.address,
                                               0),
                  account,
                  mine,
                  nonce+1)
    return tx

def calculate_optimal_sandwich():
    #  Calculate optimal sandwich
    reserves = contract_pair.functions.getReserves().call()
    attacker_frontrun = binary_search(target_amountIn, reserves[1], reserves[0],
                                      target_amountOutMin, 10 ** 10, 100, 0)
    # attacker_frontrun2 = optimal_bid2(target_amountIn, reserves[0] * reserves[1], target_amountOutMin)
    # attacker_frontrun2 -= reserves[0]
    frontrun_amountIn = int(attacker_frontrun[0] * .997)
    frontrun_amountOut = int(.997 * (frontrun_amountIn * reserves[1]) / (reserves[0] + .997 * frontrun_amountIn))
    calculated_reserves = [reserves[0] + frontrun_amountIn + target_amountIn,
                           reserves[1] - frontrun_amountOut - target_amountOutMin]
    calculated_backrunAmountOut = int(.997 * int(.997 * (frontrun_amountOut * calculated_reserves[0]) /
                                                 (calculated_reserves[1] + .997 * frontrun_amountOut)))
    return reserves, frontrun_amountIn, frontrun_amountOut, calculated_backrunAmountOut

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
ETH_ACCOUNT_FROM: LocalAccount = Account.from_key("0xdf57089febbacf7ba0bc227dafbffa9fc08a93fdc68e1e42411a14efcf23656e")
ETH_ACCOUNT_ATTACKER: LocalAccount = Account.from_key("0xde9be858da4a475276426320d5e9262ecfc3ba460bfac56360bfa6c4c28b4ee0")
ETH_ACCOUNT_TARGET: LocalAccount = Account.from_key("0x689af8efa8c651a91ad287602527f3af2fe9f6501a7ac4b061667b5a93e037fd")

# pair_json = json.load(open('../artifacts/contracts/UniswapV2Pair.sol/UniswapV2Pair.json'))
# token_json = json.load(open('../artifacts/contracts/MyToken.sol/MyToken.json'))
# factory_json = json.load(open('../artifacts/contracts/UniswapV2Factory.sol/UniswapV2Factory.json'))
# router_json = json.load(open('../artifacts/contracts/UniswapV2Router02.sol/UniswapV2Router02.json'))

# pair_json = json.load(open('../node_modules/@uniswap/v2-core/build/UniswapV2Pair.json'))
# token_json = json.load(open('../node_modules/@uniswap/v2-core/build/MyToken.json'))
# factory_json = json.load(open('../node_modules/@uniswap/v2-core/build/UniswapV2Factory.json'))
# router_json = json.load(open('../node_modules/@uniswap/v2-periphery/build/UniswapV2Router02.json'))

pair_json = json.load(open('../artifacts/contracts/UniswapV2Factory.sol/UniswapV2Pair.json'))
token_json = json.load(open('../artifacts/contracts/MyToken.sol/MyToken.json'))
factory_json = json.load(open('../artifacts/contracts/UniswapV2Factory.sol/UniswapV2Factory.json'))
router_json = json.load(open('../artifacts/contracts/UniswapV2Router02.sol/UniswapV2Router02.json'))
library_json = json.load(open('../artifacts/contracts/UniswapV2Router02.sol/UniswapV2Library.json'))

#  Deploy factory
contract_factory = deploy_contract(factory_json, mine=True, _feeToSetter=ETH_ACCOUNT_FROM.address,)

#  Deploy token
contract_token_base = deploy_contract(token_json)
contract_token_quote = deploy_contract(token_json)
print('Deployed tokens address: ', contract_token_base.address, contract_token_quote.address)

#  Transfer to attacker, target address
build_tx(contract_token_base.functions.transfer(ETH_ACCOUNT_ATTACKER.address, 500*10**18), ETH_ACCOUNT_FROM)
build_tx(contract_token_base.functions.transfer(ETH_ACCOUNT_TARGET.address, 100*10**18), ETH_ACCOUNT_FROM)

#  Deploy pair
contract_pair = build_tx(contract_factory.functions.createPair(contract_token_base.address, contract_token_quote.address),
                         ETH_ACCOUNT_FROM)
contract_pair = w3.eth.contract(w3.toChecksumAddress('0x'+contract_pair.logs[0]['data'][26:66]),
                                abi=pair_json['abi'])

print('Deployed pool address: ', contract_pair.address)

#  Deploy the router contract
contract_router = deploy_contract(router_json, _factory=contract_factory.address, _WETH= contract_token_base.address) #w3.toChecksumAddress(hex(int(contract_token_base.address, 16)-1)))

#  Approve router for tokens (all addresses)
approve_base = build_tx(contract_token_base.functions.approve(contract_router.address, 50*10**20), ETH_ACCOUNT_FROM)
approve_quote = build_tx(contract_token_quote.functions.approve(contract_router.address, 50*10**20), ETH_ACCOUNT_FROM)
approve_base = build_tx(contract_token_base.functions.approve(contract_router.address, 50*10**20), ETH_ACCOUNT_ATTACKER)
approve_quote = build_tx(contract_token_quote.functions.approve(contract_router.address, 50*10**20), ETH_ACCOUNT_ATTACKER)
approve_base = build_tx(contract_token_base.functions.approve(contract_router.address, 50*10**20), ETH_ACCOUNT_TARGET)
approve_quote = build_tx(contract_token_quote.functions.approve(contract_router.address, 50*10**20), ETH_ACCOUNT_TARGET)

#  Add liquidity
tx = build_tx(contract_router.functions.addLiquidity(contract_token_quote.address,
                                                     contract_token_base.address,
                                                     50 * 10 ** 18,
                                                     50 * 10 ** 18,
                                                     50 * 10 ** 18,
                                                     50 * 10 ** 18,
                                                     # contract_pair.address,
                                                     ETH_ACCOUNT_FROM.address,
                                                     int((dt.datetime.now()+dt.timedelta(hours=1)).timestamp())),
              ETH_ACCOUNT_FROM)


#  Test sadwich attack
#  Target amount
target_amountIn = w3.toWei(20, 'Ether')
target_amountOutMin = w3.toWei(10, 'Ether')
reserves, frontrun_amountIn, frontrun_amountOut, calculated_backrunAmountOut = calculate_optimal_sandwich()

print('BlockNum: ', w3.eth.blockNumber)
attacker_base_balance_before = contract_token_base.functions.balanceOf(ETH_ACCOUNT_ATTACKER.address).call() / 10 ** 18
attacker_quote_balance_before = contract_token_quote.functions.balanceOf(ETH_ACCOUNT_ATTACKER.address).call() / 10 ** 18
target_base_balance_before = contract_token_base.functions.balanceOf(ETH_ACCOUNT_TARGET.address).call() / 10 ** 18
target_quote_balance_before = contract_token_quote.functions.balanceOf(ETH_ACCOUNT_TARGET.address).call() / 10 ** 18

#  Frontrun tx
nonce_attacker = w3.eth.getTransactionCount(ETH_ACCOUNT_ATTACKER.address)
build_swap_pair(contract_pair, True, frontrun_amountIn, frontrun_amountOut, ETH_ACCOUNT_ATTACKER, nonce_attacker, False)
#  Target tx
nonce_target = w3.eth.getTransactionCount(ETH_ACCOUNT_TARGET.address)
build_swap_router(contract_router, True, target_amountIn, target_amountOutMin, ETH_ACCOUNT_TARGET, False)
#  Backrun tx
# reserves = contract_pair.functions.getReserves().call()
# backrun_amountIn = contract_token_quote.functions.balanceOf(ETH_ACCOUNT_ATTACKER.address).call()
# backrun_amountOut = int(.997*(backrun_amountIn*reserves[0])/(reserves[1]+.997*backrun_amountIn))
# backrun_amountOut = int(backrun_amountOut*.997)
# build_swap_pair(contract_pair, False, backrun_amountIn, backrun_amountOut, ETH_ACCOUNT_ATTACKER, nonce_attacker+2, True)
tx = build_swap_pair(contract_pair, False, frontrun_amountOut, calculated_backrunAmountOut, ETH_ACCOUNT_ATTACKER, nonce_attacker+2, True)

attacker_base_balance_after = contract_token_base.functions.balanceOf(ETH_ACCOUNT_ATTACKER.address).call() / 10 ** 18
attacker_quote_balance_after = contract_token_quote.functions.balanceOf(ETH_ACCOUNT_ATTACKER.address).call() / 10 ** 18
target_base_balance_after = contract_token_base.functions.balanceOf(ETH_ACCOUNT_TARGET.address).call() / 10 ** 18
target_quote_balance_after = contract_token_quote.functions.balanceOf(ETH_ACCOUNT_TARGET.address).call() / 10 ** 18

print('BlockNum: ', w3.eth.blockNumber)
print()
print("Attacker base amount before: ", attacker_base_balance_before)
print("Attacker quote amount before: ", attacker_quote_balance_before)
print("Target base amount before: ", target_base_balance_before)
print("Target quote amount before: ", target_quote_balance_before)
print()
print("Attacker base amount after: ", attacker_base_balance_after)
print("Attacker quote amount after: ", attacker_quote_balance_after)
print("Target base amount after: ", target_base_balance_after)
print("Target quote amount after: ", target_quote_balance_after)

