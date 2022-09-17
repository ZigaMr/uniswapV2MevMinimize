// SPDX-License-Identifier: MIT
pragma solidity =0.5.16;
import "@uniswap/v2-core/contracts/UniswapV2ERC20.sol";
contract MyToken is UniswapV2ERC20 {
    constructor()
        public {
        // ERC20 tokens have 18 decimals 
        // number of tokens minted = n * 10^18
        uint256 n = 1000;
        _mint(msg.sender, n * 10**18);
    }
}