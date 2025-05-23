// scripts/deploy.js
const hre = require("hardhat");
async function main() {
  const Bulletin = await hre.ethers.getContractFactory("AgeTokenBulletin");
  const bulletin = await Bulletin.deploy(
      "0x" + "00".repeat(32) // placeholder thumb-print
  );
  await bulletin.deployed();
  console.log("Bulletin deployed:", bulletin.address);
}
main()
  .then(()=>process.exit(0))
  .catch(err=>{console.error(err);process.exit(1);});
