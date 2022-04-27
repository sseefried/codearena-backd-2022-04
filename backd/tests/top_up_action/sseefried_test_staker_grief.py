import pytest
import brownie
from brownie import AliceAttacker, BobAttacker
from brownie.test.managers.runner import RevertContextManager as reverts
from support.constants import ADMIN_DELAY, AddressProviderKeys
from support.contract_utils import update_topup_handler
from support.types import TopUpRecord
from support.utils import encode_account, scale
from support.convert import format_to_bytes

MOCK_PROTOCOL_NAME = format_to_bytes("mock", 32)
TOPUP_FEE = scale("0.02")

pytestmark = pytest.mark.usefixtures(
    "registerSetUp",
    "curveInitialLiquidity",
    "vault",
    "mintAlice",
    "approveAlice",
    "curveInitialLiquidity",
)


@pytest.fixture
def registerSetUp(chain, topUpAction, address_provider, admin, pool, mockTopUpHandler):
    address_provider.addPool(pool, {"from": admin})
    update_topup_handler(
        topUpAction, MOCK_PROTOCOL_NAME, mockTopUpHandler, chain, admin
    )
    topUpAction.setActionFee(TOPUP_FEE, {"from": admin})

@pytest.fixture
def mockErc20Coin(MockErc20, admin):
    return admin.deploy(MockErc20, 18)


@pytest.fixture
def swapperSetup(
    admin, address_provider, coin, swapperRegistry, mockSwapper, mockErc20Coin, chain
):
    mockErc20Coin.mint_for_testing(mockSwapper, 1_000_000 * 1e18)
    swapperRegistry.registerSwapper(coin, mockErc20Coin, mockSwapper)
    address_provider.initializeAddress(
        AddressProviderKeys.SWAPPER_REGISTRY.value, swapperRegistry, {"from": admin}
    )


def _create_position(on_behalf_of, threshold, coin, payer, topUpAction, pool, lpToken):
    decimals = coin.decimals()
    single_topup_amount = scale(2, decimals)
    total_topup_amount = scale(2, decimals)

    deposit_amount = total_topup_amount * 2
    pool.deposit(deposit_amount, {"from": payer})

    lpToken.approve(topUpAction, total_topup_amount, {"from": payer})
    max_gas_price = scale(30, 9)
    topup_count = (total_topup_amount + single_topup_amount - 1) // single_topup_amount
    gas_deposit = max_gas_price * topup_count * topUpAction.getEstimatedGasUsage()
    record = TopUpRecord(
        threshold=scale(threshold),
        priorityFee=scale(1, 9),
        maxFee=max_gas_price,
        actionToken=coin,
        depositToken=lpToken,
        singleTopUpAmount=single_topup_amount,
        totalTopUpAmount=total_topup_amount,
    )
    topUpAction.register(
        encode_account(on_behalf_of),
        MOCK_PROTOCOL_NAME,
        total_topup_amount,
        record,
        {"from": payer, "value": gas_deposit},
    )
    return record

def test_topup(admin, chain, alice, bob, topUpAction, coin, lpToken, pool, gas_bank, initialAmount):
    aliceAttacker = admin.deploy(AliceAttacker, amount = 1e18);
    coin.mint_for_testing(aliceAttacker, initialAmount, {"from": admin})
    coin.approve(pool, 2**256 - 1, {"from": aliceAttacker})


    single_topup_amount = scale(2, coin.decimals())

    record = _create_position(alice, "1.5", coin, aliceAttacker, topUpAction, pool, lpToken)

    # aliceAttacker.setCanReceive(False)

    bob_balance_before = bob.balance()

    with brownie.reverts("Alice griefed"):
        topUpAction.execute(
            aliceAttacker,
            encode_account(alice),
            bob,
            MOCK_PROTOCOL_NAME,
            {"from": bob, "priority_fee": record.priorityFee},
        ) # will revert

    print(tx.info())

    bob_balance_after = bob.balance()
    print("bob before", bob_balance_before)
    print("bob after", bob_balance_after)
    assert 1 == 2

#     previous_gas_balance = gas_bank.balanceOf(alice)
#     print("bob before", bobAttacker.balance())



#     tx = bobAttacker.attack();

#     # tx = topUpAction.execute(
#     #     alice,
#     #     encode_account(alice),
#     #     bobAttacker,
#     #     MOCK_PROTOCOL_NAME,
#     #     {"from": bob, "priority_fee": record.priorityFee},
#     # )

#     print("bob after ", bobAttacker.balance())
#     print(tx.info())
# #    assert tx.gas_price == chain.base_fee + record.priorityFee

#     new_gas_balance = gas_bank.balanceOf(alice)

# #    assert new_gas_balance < previous_gas_balance

#     gas_bank_withdraw_event = tx.events["Withdraw"][0]
#     assert gas_bank_withdraw_event["account"] == alice
# #    assert gas_bank_withdraw_event["value"] == previous_gas_balance - new_gas_balance

#     gas_consumed = gas_bank_withdraw_event["value"] // tx.gas_price
#     print(tx.events["Log"])
#     print("record.priorityFee", record.priorityFee)
#     print("gas_bank_withdraw_event[\"value\"]",  gas_bank_withdraw_event["value"])
#     print("gas_consumed", gas_consumed)
#     print("tx.gas_price", tx.gas_price)
#     print("tx.gas_used", tx.gas_used)

#     # FIXME: this should succeed but for some reason does not
#     # assert gas_consumed < tx.gas_used

#     execute_event = tx.events["TopUp"][0]
#     assert execute_event["topupAmount"] == single_topup_amount
#     amount_with_fees = single_topup_amount * (scale(1) + TOPUP_FEE) / scale(1)
#     assert execute_event["consumedDepositAmount"] == amount_with_fees
#     new_user_factor = topUpAction.getHealthFactor(
#         MOCK_PROTOCOL_NAME, encode_account(alice), b""
#     )
#     # mock version starts at 1.3 and has +0.3 if topup is succesful
#     assert new_user_factor == scale("1.6")
#     assert 1 == 2