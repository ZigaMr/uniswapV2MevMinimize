# MEV resistant DEX (Uniswap v2 fork)

### About:
An attempt to try and mitigate the negative effects of frontrunning attacks on Ethereum and other EVM based decentralized exchanges.
The bulk of of all MEV (maximal extractable value) can be categorized into 3 groups:

- Sandwich attacks (frontrun an order tx by buying and selling accordingly as to gain risk-free profit at the expense of high slippage)
- Arbitrage (take advantage of price imbalance between different exchanges)
- Liquidations (close (liquidate) positions when price negatively affects borrowed assets, sell off the collateral, return the borrowed asset and keep the change)

The purpose of this project is to try and prevent Sandwich attacks on a cloned Uniswap v2 exchange.

### Overview
Consider a scenario where an attacker can "squeeze" a target transaction inbetween his buy and sell txs.




```shell
npx hardhat help
npx hardhat test
GAS_REPORT=true npx hardhat test
npx hardhat node
npx hardhat run scripts/deploy.js
```
