const hre = require("hardhat");

async function main() {
  const Bulletin = await hre.ethers.getContractFactory("AgeTokenBulletin");
  
  // Deploy with initial thumbprint (32 zero bytes)
  const bulletin = await Bulletin.deploy("0x" + "00".repeat(32));
  
  // Wait for deployment to complete
  await bulletin.waitForDeployment();
  
  const address = await bulletin.getAddress();
  console.log("AgeTokenBulletin deployed to:", address);
}

main()
  .then(() => process.exit(0))
  .catch((err) => {
    console.error(err);
    process.exit(1);
  });
