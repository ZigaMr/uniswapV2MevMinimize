/** @type import('hardhat/config').HardhatUserConfig */
// require("@nomiclabs/hardhat-ethers");

module.exports = {
    solidity: {
        compilers: [
            {
                version: "0.5.16",
                settings: {optimizer: {enabled: true, runs: 5}},
            },
            {
                version: "0.5.17",
            },
            {
                version: "0.6.6",
                settings: {optimizer: {enabled: true, runs: 5}},
            },
            {
                version: "0.8.10",
            },
        ],
    },
    networks: {
        hardhat: {
            mining:{
                auto: false,
                interval: 0,
                // mempool:{
                //     order: "fifo"
                // }
            }
        }
    }
};
