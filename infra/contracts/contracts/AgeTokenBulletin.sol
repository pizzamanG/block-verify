// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract AgeTokenBulletin {
    bytes32 public thumbprint;
    bytes32 public revocationRoot;

    address public immutable issuer;

    constructor(bytes32 _thumbprint) {
        issuer = msg.sender;
        thumbprint = _thumbprint;
    }

    function setThumbprint(bytes32 _thumbprint) external {
        require(msg.sender == issuer, "Not issuer");
        thumbprint = _thumbprint;
    }

    function setRevocationRoot(bytes32 _root) external {
        require(msg.sender == issuer, "Not issuer");
        revocationRoot = _root;
    }
}
