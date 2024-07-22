// SPDX-License-Identifier: MIT
pragma solidity ^0.8.17;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "./BridgeToken.sol";

contract Destination is AccessControl {
    bytes32 public constant WARDEN_ROLE = keccak256("BRIDGE_WARDEN_ROLE");
    bytes32 public constant CREATOR_ROLE = keccak256("CREATOR_ROLE");
	mapping( address => address) public underlying_tokens;
	mapping( address => address) public wrapped_tokens;
	address[] public tokens;

	event Creation( address indexed underlying_token, address indexed wrapped_token );
	event Wrap( address indexed underlying_token, address indexed wrapped_token, address indexed to, uint256 amount );
	event Unwrap( address indexed underlying_token, address indexed wrapped_token, address frm, address indexed to, uint256 amount );

    constructor( address admin ) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(CREATOR_ROLE, admin);
        _grantRole(WARDEN_ROLE, admin);
    }

function wrap(address _underlying_token, address _recipient, uint256 _amount ) public onlyRole(WARDEN_ROLE) {
= 
    address wrapped_token_address = wrapped_tokens[_underlying_token];
    require(wrapped_token_address != address(0), "Token not registered");  
    BridgeToken wrappedToken = BridgeToken(wrapped_token_address);
    wrappedToken.mint(_recipient, _amount);


    emit Wrap(_underlying_token, wrapped_token_address, _recipient, _amount);
}


function unwrap(address _wrapped_token, address _recipient, uint256 _amount ) public {

    BridgeToken wrappedToken = BridgeToken(_wrapped_token);
    address underlying_token = wrappedToken.underlying();


    require(wrappedToken.balanceOf(msg.sender) >= _amount, "Insufficient balance");


    wrappedToken.burnFrom(msg.sender, _amount);


    emit Unwrap(underlying_token, _wrapped_token, msg.sender, _recipient, _amount);
}


function createToken(address _underlying_token, string memory name, string memory symbol ) public onlyRole(CREATOR_ROLE) returns(address) {

    require(wrapped_tokens[_underlying_token] == address(0), "Token already exists");

    BridgeToken wrappedToken = new BridgeToken(_underlying_token, name, symbol, msg.sender);
    address wrapped_token_address = address(wrappedToken);


    underlying_tokens[_underlying_token] = wrapped_token_address;
    wrapped_tokens[_underlying_token] = wrapped_token_address;
    tokens.push(_underlying_token);

    emit Creation(_underlying_token, wrapped_token_address);

    return wrapped_token_address;
}

}


