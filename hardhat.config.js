require("@nomicfoundation/hardhat-toolbox");

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.9",
networks: {
  hardhat: {
    forking: {
      url: "https://eth-mainnet.alchemyapi.io/v2/okafFkPHMhqVc1MA5D-pgqL2XdIhE-pp",
      blockNumber: 14602783
    }
  }
}
};