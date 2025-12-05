// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CopyrightRegistry {
    struct Record {
        string cid;
        address owner;
        uint256 timestamp;
    }

    mapping(string => Record) public records;
    string[] public allCIDs;

    function storeRecord(string memory cid) public {
        require(records[cid].owner == address(0), "Already registered");

        records[cid] = Record({
            cid: cid,
            owner: msg.sender,
            timestamp: block.timestamp
        });

        allCIDs.push(cid);
    }

    function verifyRecord(string memory cid) public view returns (address, uint256) {
        return (records[cid].owner, records[cid].timestamp);
    }

    function getAllRecords() public view returns (Record[] memory) {
        Record[] memory output = new Record[](allCIDs.length);

        for (uint256 i = 0; i < allCIDs.length; i++) {
            output[i] = records[allCIDs[i]];
        }

        return output;
    }
}
