// SPDX-License-Identifier: UNLICENSED
pragma solidity 0.8.9;

import "../../../interfaces/actions/topup/ITopUpAction.sol";
import "../interfaces/IGasBank.sol";

contract AliceAttacker { 

    bool canReceive = true;

    event Log(string msg);

    constructor() payable { 

    }

    function setCanReceive(bool _canReceive) public { 
        canReceive = _canReceive;
    }

    receive() external payable {
        emit Log("receive was called");
        if (!canReceive) {
            revert("Alice griefed");
        }
    }

}