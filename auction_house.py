import smartpy as sp

class FA2ErrorMessage:
    PREFIX = "FA2_"
    TOKEN_UNDEFINED = "{}TOKEN_UNDEFINED".format(PREFIX)
    INSUFFICIENT_BALANCE = "{}INSUFFICIENT_BALANCE".format(PREFIX)
    NOT_OWNER = "{}NOT_OWNER".format(PREFIX)

class LedgerKey:
    def get_type():
        return sp.TRecord(owner = sp.TAddress, token_id = sp.TNat).layout(( "owner", "token_id"))

    def make(owner, token_id):
        return sp.set_type_expr(sp.record(owner = owner, token_id = token_id), LedgerKey.get_type())

class BatchTransfer:
    def get_transfer_type():
        tx_type = sp.TRecord(to_ = sp.TAddress,
                             token_id = sp.TNat,
                             amount = sp.TNat).layout(
                ("to_", ("token_id", "amount"))
            )
        transfer_type = sp.TRecord(from_ = sp.TAddress,
                                   txs = sp.TList(tx_type)).layout(
                                       ("from_", "txs"))
        return transfer_type

    def get_type():
        return sp.TList(BatchTransfer.get_transfer_type())

    def item(from_, txs):
        return sp.set_type_expr(sp.record(from_ = from_, txs = txs), BatchTransfer.get_transfer_type())

class BalanceOfRequest:
    def get_response_type():
        return sp.TList(
            sp.TRecord(
                request = LedgerKey.get_type(),
                balance = sp.TNat).layout(("request", "balance")))
    def get_type():
        return sp.TRecord(
            requests = sp.TList(LedgerKey.get_type()),
            callback = sp.TContract(BalanceOfRequest.get_response_type())
        ).layout(("requests", "callback"))

class AllowanceKey:
    def get_type():
        return sp.TRecord(owner = sp.TAddress, operator = sp.TAddress, token_id = sp.TNat).layout(("owner", ("operator","token_id")))

    def make(owner, operator, token_id):
        return sp.set_type_expr(sp.record(owner = owner, operator = operator, token_id = token_id), AllowanceKey.get_type())

class BatchApprove:
    def get_type():
        return sp.TList(sp.TRecord(operator = sp.TAddress,
                             token_id = sp.TNat,
                             amount = sp.TNat).layout(
                ("operator", ("token_id", "amount"))
            ))

class BatchInitialAuction:
    def get_type():
        return sp.TRecord(
            auction_id_start = sp.TNat,
            token_ids = sp.TList(sp.TNat)
        ).layout(
            ("auction_id_start","token_ids")
            )


class AuctionErrorMessage:
    PREFIX = "AUC_"
    ID_ALREADY_IN_USE = "{}ID_ALREADY_IN_USE".format(PREFIX)
    SELLER_CANNOT_BID = "{}SELLER_CANNOT_BID".format(PREFIX)
    BID_AMOUNT_TOO_LOW = "{}BID_AMOUNT_TOO_LOW".format(PREFIX)
    AUCTION_IS_OVER = "{}AUCTION_IS_OVER".format(PREFIX)
    AUCTION_IS_ONGOING = "{}AUCTION_IS_ONGOING".format(PREFIX)
    SENDER_NOT_BIDDER = "{}SENDER_NOT_BIDDER".format(PREFIX)
    TOKEN_AMOUNT_TOO_LOW = "{}TOKEN_AMOUNT_TOO_LOW".format(PREFIX)
    END_DATE_TOO_SOON = "{}END_DATE_TOO_SOON".format(PREFIX)
    END_DATE_TOO_LATE = "{}END_DATE_TOO_LATE".format(PREFIX)

class Auction():
    def get_type():
        return sp.TRecord(token_address=sp.TAddress, token_id=sp.TNat, token_amount=sp.TNat,  end_timestamp=sp.TTimestamp, seller=sp.TAddress, bid_amount=sp.TMutez, bidder=sp.TAddress).layout(("token_address",("token_id",("token_amount",("end_timestamp",("seller",("bid_amount","bidder")))))))

class AuctionCreateRequest():
    def get_type():
        return sp.TRecord(auction_id=sp.TNat,token_address=sp.TAddress, token_id=sp.TNat, token_amount=sp.TNat,  end_timestamp=sp.TTimestamp,  bid_amount=sp.TMutez)#.layout(("auction_id",("token_address",("token_id",("token_amount",("end_timestamp","bid_amount"))))))

class UpdateOperatorsRequest():
    def get_operator_param_type():
        return sp.TRecord(
            owner = sp.TAddress,
            operator = sp.TAddress,
            token_id = sp.TNat
            ).layout(("owner", ("operator", "token_id")))
    def get_type():
        return sp.TList(
                sp.TVariant(
                    add_operator = UpdateOperatorsRequest.get_operator_param_type(),
                    remove_operator = UpdateOperatorsRequest.get_operator_param_type())
        )

INITIAL_BID = sp.mutez(900000)
MINIMAL_BID = sp.mutez(100000)
INITIAL_AUCTION_DURATION = sp.int(24*5)
MINIMAL_AUCTION_DURATION = sp.int(1)
MAXIMAL_AUCTION_DURATION = sp.int(24*7)
MAXIMAL_TOKEN_ID = sp.nat(1689)
THRESHOLD_ADDRESS = sp.address("tz3jfebmewtfXYD1Xef34TwrfMg2rrrw6oum") # this is the biggest tz3 after this only KT...
DEFAULT_ADDRESS = sp.address("tz1RKmJwoAiaqFdjQYSbFy1j7u7UhEFsqXq7")
AUCTION_EXTENSION_THRESHOLD = sp.int(60*5) # 5 minutes
BID_STEP_THRESHOLD = sp.mutez(100000)

class TZColorsFA2(sp.Contract):
    def __init__(self, initial_auction_house_address):
        self.init(
            initial_auction_house_address = initial_auction_house_address,
            ledger = sp.big_map(tkey=LedgerKey.get_type(), tvalue=sp.TNat),
            token_metadata = sp.bytes('0x697066733a2f2f516d5477794e383547667a6942354247684632454c6f67654a527436437765765a5937323962616851714b486944'),
            total_supply=sp.big_map(tkey=sp.TNat, tvalue = sp.TNat),
            allowances = sp.big_map(tkey=AllowanceKey.get_type(), tvalue=sp.TBool)
        )

    @sp.entry_point
    def initial_auction(self, batch_initial_auction):
        sp.set_type_expr(batch_initial_auction, BatchInitialAuction.get_type())
        auction_id_runner = sp.local('auction_id_runner', batch_initial_auction.auction_id_start)
        sp.for token_id in batch_initial_auction.token_ids:
            sp.verify((~self.data.total_supply.contains(token_id)), message = FA2ErrorMessage.NOT_OWNER)
            sp.verify(token_id<=MAXIMAL_TOKEN_ID, message = FA2ErrorMessage.NOT_OWNER)
            to_user = LedgerKey.make(sp.self_address, token_id)
            self.data.ledger[to_user] = sp.nat(1)
            self.data.total_supply[token_id] = sp.nat(1)
            operator_user = AllowanceKey.make(sp.self_address, self.data.initial_auction_house_address, token_id)
            self.data.allowances[operator_user] = True
            auction_house = sp.contract(AuctionCreateRequest.get_type(), self.data.initial_auction_house_address, entry_point = "create_auction").open_some()
            auction_create_request = sp.record(
                auction_id=auction_id_runner.value,
                token_address=sp.self_address,
                token_id=token_id,
                token_amount=sp.nat(1),
                end_timestamp=sp.now.add_hours(INITIAL_AUCTION_DURATION),
                bid_amount=INITIAL_BID
            )
            sp.set_type_expr(auction_create_request, AuctionCreateRequest.get_type())
            sp.transfer(auction_create_request, sp.mutez(0), auction_house)
            auction_id_runner.value += 1

    @sp.entry_point
    def update_operators(self, update_operator_requests):
        sp.set_type(update_operator_requests,UpdateOperatorsRequest.get_type())
        sp.for update_operator_request in update_operator_requests:
            with update_operator_request.match_cases() as argument:
                with argument.match("add_operator") as update:
                    sp.verify(update.owner == sp.sender, message=FA2ErrorMessage.NOT_OWNER)
                    operator_user = AllowanceKey.make(update.owner, update.operator, update.token_id)
                    self.data.allowances[operator_user] = True
                with argument.match("remove_operator") as update:
                    sp.verify(update.owner == sp.sender, message=FA2ErrorMessage.NOT_OWNER)
                    operator_user = AllowanceKey.make(update.owner, update.operator, update.token_id)
                    del self.data.allowances[operator_user]

    @sp.entry_point
    def transfer(self, batch_transfers):
        sp.set_type(batch_transfers, BatchTransfer.get_type())
        sp.for transfer in batch_transfers:
           sp.for tx in transfer.txs:
                sp.if (tx.amount > sp.nat(0)):
                    from_user = LedgerKey.make(transfer.from_, tx.token_id)
                    to_user = LedgerKey.make(tx.to_, tx.token_id)

                    sp.verify((self.data.ledger.get(from_user,sp.nat(0)) >= tx.amount), message = FA2ErrorMessage.INSUFFICIENT_BALANCE)

                    operator_user = AllowanceKey.make(transfer.from_, sp.sender, tx.token_id)

                    sp.verify(((sp.sender == transfer.from_) | self.data.allowances.get(operator_user, False)), message=FA2ErrorMessage.NOT_OWNER)
                    self.data.ledger[from_user] = sp.as_nat(self.data.ledger[from_user] - tx.amount)
                    self.data.ledger[to_user] = self.data.ledger.get(to_user, 0) + tx.amount

                    sp.if sp.sender != transfer.from_:
                        del self.data.allowances[operator_user]

                    sp.if self.data.ledger.get(from_user,sp.nat(0)) == sp.nat(0):
                        del self.data.ledger[from_user]

    @sp.entry_point
    def balance_of(self, balance_of_request):
        sp.set_type(balance_of_request, BalanceOfRequest.get_type())

        responses = sp.local("responses", sp.set_type_expr(sp.list([]),BalanceOfRequest.get_response_type()))
        sp.for request in balance_of_request.requests:
            responses.value.push(sp.record(request = request, balance = self.data.ledger.get(LedgerKey.make(request.owner, request.token_id),0)))

        sp.transfer(responses.value, sp.mutez(0), balance_of_request.callback)

class AuctionHouse(sp.Contract):
    def __init__(self):
        self.init(auctions=sp.big_map(tkey=sp.TNat, tvalue = Auction.get_type()))

    @sp.entry_point
    def create_auction(self, create_auction_request):
        sp.set_type_expr(create_auction_request, AuctionCreateRequest.get_type())
        token_contract = sp.contract(BatchTransfer.get_type(), create_auction_request.token_address, entry_point = "transfer").open_some()
        sp.verify(create_auction_request.token_amount > 0, message=AuctionErrorMessage.TOKEN_AMOUNT_TOO_LOW)
        sp.verify(create_auction_request.end_timestamp  >= sp.now.add_hours(MINIMAL_AUCTION_DURATION), message=AuctionErrorMessage.END_DATE_TOO_SOON)
        sp.verify(create_auction_request.end_timestamp  <= sp.now.add_hours(MAXIMAL_AUCTION_DURATION), message=AuctionErrorMessage.END_DATE_TOO_LATE)
        sp.verify(create_auction_request.bid_amount >= MINIMAL_BID, message=AuctionErrorMessage.BID_AMOUNT_TOO_LOW)
        sp.verify(~self.data.auctions.contains(create_auction_request.auction_id), message=AuctionErrorMessage.ID_ALREADY_IN_USE)

        sp.transfer([BatchTransfer.item(sp.sender, [sp.record(to_=sp.self_address, token_id=create_auction_request.token_id, amount=create_auction_request.token_amount)])], sp.mutez(0), token_contract)
        self.data.auctions[create_auction_request.auction_id] = sp.record(token_address=create_auction_request.token_address, token_id=create_auction_request.token_id, token_amount=create_auction_request.token_amount, end_timestamp=create_auction_request.end_timestamp, seller=sp.sender, bid_amount=create_auction_request.bid_amount, bidder=sp.sender)

    @sp.entry_point
    def bid(self, auction_id):
        sp.set_type_expr(auction_id, sp.TNat)
        auction = self.data.auctions[auction_id]

        sp.verify(sp.sender!=auction.seller, message=AuctionErrorMessage.SELLER_CANNOT_BID)
        sp.verify(sp.amount>=auction.bid_amount+BID_STEP_THRESHOLD, message=AuctionErrorMessage.BID_AMOUNT_TOO_LOW)
        sp.verify(sp.now<auction.end_timestamp, message=AuctionErrorMessage.AUCTION_IS_OVER)

        sp.if auction.bidder != auction.seller:
            sp.if auction.bidder>THRESHOLD_ADDRESS:
                sp.send(DEFAULT_ADDRESS, auction.bid_amount)
            sp.else:
                sp.send(auction.bidder, auction.bid_amount)

        auction.bidder = sp.sender
        auction.bid_amount = sp.amount
        sp.if auction.end_timestamp-sp.now < AUCTION_EXTENSION_THRESHOLD:
            auction.end_timestamp = sp.now.add_seconds(AUCTION_EXTENSION_THRESHOLD)
        self.data.auctions[auction_id] = auction

    @sp.entry_point
    def withdraw(self, auction_id):
        sp.set_type_expr(auction_id, sp.TNat)
        auction = self.data.auctions[auction_id]

        sp.verify(sp.now>auction.end_timestamp,message=AuctionErrorMessage.AUCTION_IS_ONGOING)

        token_contract = sp.contract(BatchTransfer.get_type(), auction.token_address, entry_point = "transfer").open_some()

        sp.if auction.bidder != auction.seller:
            sp.if auction.seller>THRESHOLD_ADDRESS:
               sp.send(DEFAULT_ADDRESS, auction.bid_amount)
            sp.else:
               sp.send(auction.seller, auction.bid_amount)

        sp.transfer([BatchTransfer.item(sp.self_address,[sp.record(to_=auction.bidder, token_id=auction.token_id, amount=auction.token_amount)])], sp.mutez(0), token_contract)
        del self.data.auctions[auction_id]

@sp.add_test(name = "Auction House")
def test():
    scenario = sp.test_scenario()
    scenario.h1("Auction House")
    scenario.table_of_contents()

    admin = sp.test_account("Administrator")
    alice = sp.test_account("Alice")
    bob = sp.test_account("Robert")
    dan = sp.test_account("Dan")

    # Let's display the accounts:
    scenario.h2("Accounts")
    scenario.show([admin, alice, bob, dan])

    auction_house = AuctionHouse()
    scenario += auction_house

    scenario.h2("TZColorsFA2")
    fa2 = TZColorsFA2(auction_house.address)#sp.address("KT1CpeSQKdkhWi4pinYcseCFKmDhs5M74BkU"))
    scenario += fa2

    scenario.h2("Initial Auction")

    scenario.p("Kick-off initial Auctions")
    scenario += fa2.initial_auction(auction_id_start=sp.nat(0),token_ids=[sp.nat(0),sp.nat(1),sp.nat(2)]).run(sender=admin)

    scenario.p("Try to re-auction existing stuff")
    scenario += fa2.initial_auction(auction_id_start=sp.nat(0),token_ids=[sp.nat(0),sp.nat(1),sp.nat(2)]).run(sender=admin, valid=False)

    scenario.p("Bob bids")
    scenario += auction_house.bid(0).run(sender=bob,amount=sp.mutez(2000000), now=sp.timestamp(0).add_minutes(1))

    scenario.p("Dan bids")
    scenario += auction_house.bid(0).run(sender=dan,amount=sp.mutez(3000000), now=sp.timestamp(0).add_minutes(2))

    scenario.p("Bob rebids")
    scenario += auction_house.bid(0).run(sender=bob,amount=sp.mutez(4000000), now=sp.timestamp(0).add_minutes(3))

    scenario.p("Bob withdraws")
    scenario += auction_house.withdraw(0).run(sender=bob,amount=sp.mutez(2000000), now=sp.timestamp(0).add_minutes(5).add_days(5))

    scenario.p("Bob updates operators")
    scenario += fa2.update_operators([sp.variant('add_operator', sp.record(owner=bob.address,operator=auction_house.address,token_id=sp.nat(0)))]).run(sender=bob)

    scenario.h2("User Auction")
    scenario.p("Bob creates auction")
    auction_id = sp.nat(0) # we can reuse 0
    scenario += auction_house.create_auction(sp.record(auction_id=auction_id, token_address=fa2.address, token_id=sp.nat(0), token_amount=sp.nat(1),  end_timestamp=sp.timestamp(60*60),  bid_amount=sp.mutez(100000))).run(sender=bob, now=sp.timestamp(0))

    scenario.p("Bob tries to withdraw")
    scenario += auction_house.withdraw(0).run(sender=bob, amount=sp.mutez(0), now=sp.timestamp(0), valid=False)

    scenario.p("Alice bids")
    scenario += auction_house.bid(0).run(sender=alice,amount=sp.mutez(200000), now=sp.timestamp(0))

    scenario.p("Dan bids")
    scenario += auction_house.bid(0).run(sender=dan,amount=sp.mutez(300000), now=sp.timestamp(1))

    scenario.p("Alice rebids")
    scenario += auction_house.bid(0).run(sender=alice,amount=sp.mutez(400000), now=sp.timestamp(2))

    scenario.p("Bob tries to withdraw")
    scenario += auction_house.withdraw(0).run(sender=bob, amount=sp.mutez(0), now=sp.timestamp(60*60), valid=False)

    scenario.p("Dan bids")
    scenario += auction_house.bid(0).run(sender=dan,amount=sp.mutez(500000), now=sp.timestamp(60*60-5))

    scenario.p("Alice rebids")
    scenario += auction_house.bid(0).run(sender=alice,amount=sp.mutez(600000), now=sp.timestamp(60*60+5*60-6))

    scenario.p("Alice withdraws")
    scenario += auction_house.withdraw(0).run(sender=alice, amount=sp.mutez(0), now=sp.timestamp(60*60+5*60-6+5*60+1))

    scenario.h2("Self-Withdraw")
    scenario.p("Alice creates auction")
    auction_id = sp.nat(0) # we can reuse 0
    scenario += fa2.update_operators([sp.variant('add_operator', sp.record(owner=alice.address,operator=auction_house.address,token_id=sp.nat(0)))]).run(sender=alice)
    scenario += auction_house.create_auction(sp.record(auction_id=auction_id, token_address=fa2.address, token_id=sp.nat(0), token_amount=sp.nat(1),  end_timestamp=sp.timestamp(60*60),  bid_amount=sp.mutez(100000))).run(sender=alice, now=sp.timestamp(0))

    scenario.p("Bob funds in parallel another auction")
    scenario += fa2.initial_auction(auction_id_start=sp.nat(10),token_ids=[sp.nat(4),sp.nat(5),sp.nat(6)]).run(sender=admin)
    scenario.p("Bob bids")
    scenario += auction_house.bid(10).run(sender=bob, amount=sp.mutez(1000000), now=sp.timestamp(0))
    scenario.p("Alice withdraws (something that had minimal bid, but nobody who bidded)")
    scenario += auction_house.withdraw(0).run(sender=alice, amount=sp.mutez(0), now=sp.timestamp(3+60*60))

    scenario.p("Bob withdraws")
    scenario += auction_house.withdraw(10).run(sender=bob,  now=sp.timestamp(1+5*24*60*60))

    scenario.h2("Self-Bid")
    scenario.p("Bob creates auction")
    auction_id = sp.nat(0) # we can reuse 0
    scenario += fa2.update_operators([sp.variant('add_operator', sp.record(owner=bob.address,operator=auction_house.address,token_id=sp.nat(4)))]).run(sender=bob)
    scenario += auction_house.create_auction(sp.record(auction_id=auction_id, token_address=fa2.address, token_id=sp.nat(4), token_amount=sp.nat(1),  end_timestamp=sp.timestamp(60*60),  bid_amount=sp.mutez(100000))).run(sender=bob, now=sp.timestamp(0))

    scenario += auction_house.bid(0).run(sender=bob, amount=sp.mutez(200000), valid=False, now=sp.timestamp(2))
    scenario += auction_house.withdraw(0).run(sender=bob,  now=sp.timestamp(1+5*24*60*60))

    scenario.h2("Existing Auctions")
    scenario.p("Bob creates auction with same id")
    scenario += fa2.update_operators([sp.variant('add_operator', sp.record(owner=bob.address,operator=auction_house.address,token_id=sp.nat(4)))]).run(sender=bob)
    scenario += auction_house.create_auction(sp.record(auction_id=1, token_address=fa2.address, token_id=sp.nat(4), token_amount=sp.nat(1),  end_timestamp=sp.timestamp(60*60),  bid_amount=sp.mutez(100000))).run(sender=bob, now=sp.timestamp(0), valid=False)

    scenario.h2("Transfers")
    scenario.p("Bob cannot transfer alice's token")
    auction_id = sp.nat(0) # we can reuse 0
    scenario += fa2.transfer([BatchTransfer.item(alice.address, [sp.record(to_=bob.address, token_id=0, amount=1)])]).run(sender=bob, valid=False)
    scenario.p("Alice can transfer own token")
    auction_id = sp.nat(0) # we can reuse 0
    scenario += fa2.transfer([BatchTransfer.item(alice.address, [sp.record(to_=bob.address, token_id=0, amount=1)])]).run(sender=alice)

    scenario.p("Bob cannot transfer more token")
    auction_id = sp.nat(0) # we can reuse 0
    scenario += fa2.transfer([BatchTransfer.item(bob.address, [sp.record(to_=bob.address, token_id=0, amount=2)])]).run(sender=bob, valid=False)

    scenario.p("Bob cannot transfer from non balance address")
    auction_id = sp.nat(0) # we can reuse 0
    scenario += fa2.transfer([BatchTransfer.item(alice.address, [sp.record(to_=dan.address, token_id=0, amount=1)])]).run(sender=bob, valid=False)

    scenario.p("Bob can transfer as owner")
    auction_id = sp.nat(0) # we can reuse 0
    scenario += fa2.transfer([BatchTransfer.item(bob.address, [sp.record(to_=dan.address, token_id=0, amount=1)])]).run(sender=bob)

    scenario.p("Try to re-auction existing stuff")
    scenario += fa2.initial_auction(auction_id_start=sp.nat(0),token_ids=[sp.nat(0),sp.nat(1),sp.nat(2)]).run(sender=admin, valid=False)

    scenario.p("Try large token id")
    scenario += fa2.initial_auction(auction_id_start=sp.nat(123),token_ids=[sp.nat(1689)]).run(sender=admin)

    scenario.p("Try too large token id")
    scenario += fa2.initial_auction(auction_id_start=sp.nat(124),token_ids=[sp.nat(1690)]).run(sender=admin, valid=False)
