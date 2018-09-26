from dataclasses import dataclass, field
from datetime import datetime as dt
from decimal import Decimal
from enum import Enum
from typing import Any, List, Optional, Tuple, Union

import maya
from cached_property import cached_property

from trading_bots.contrib.money import Money
from .errors import OrderBookEmpty, QuotationError
from .utils import parse_money

__all__ = [
    'Number',
    'Money',
    'Market',
    'Side',
    'OrderType',
    'OrderStatus',
    'TxType',
    'TxStatus',
    'Ticker',
    'Balance',
    'Trade',
    'Order',
    'OrderBookEntry',
    'OrderBook',
    'OrderBookSide',
    'Transaction',
    'Withdrawal',
    'Deposit',
]

Number = Union[int, Decimal, Money]


class Market:

    def __init__(self, base: str, quote: str):
        self._base = str(base)
        self._quote = str(quote)

    @property
    def base(self) -> str:
        return self._base

    @property
    def quote(self) -> str:
        return self._quote

    @property
    def code(self) -> str:
        return self.base + self.quote

    @classmethod
    def from_code(cls, code: str):
        assert len(code) == 6, 'A market code must have 6 characters (base and quote currency).'
        base, quote = code[:3], code[3:]
        return cls(base, quote)

    def __repr__(self) -> str:
        return self.code

    def __hash__(self) -> int:
        return hash(self.code)

    def __str__(self) -> str:
        return str(self.code)

    def __lt__(self, other: (str, 'Market')) -> bool:
        if isinstance(other, Market):
            other = other.code
        return self.code < other

    def __lte__(self, other: (str, 'Market')) -> bool:
        if isinstance(other, Market):
            other = other.code
        return self.code <= other

    def __gt__(self, other: (str, 'Market')) -> bool:
        if isinstance(other, Market):
            other = other.code
        return self.code > other

    def __gte__(self, other: (str, 'Market')) -> bool:
        if isinstance(other, Market):
            other = other.code
        return self.code >= other

    def __eq__(self, other: (str, 'Market')) -> bool:
        if isinstance(other, Market):
            other = other.code
        return self.code == other

    def __ne__(self, other: (str, 'Market')) -> bool:
        if isinstance(other, Market):
            other = other.code
        return not self.code == other

    def __bool__(self) -> bool:
        return bool(self.code)


class Side(Enum):
    BUY = 'buy'
    SELL = 'sell'

    def __repr__(self):
        return self.name

    @property
    def type(self):
        if self == Side.BUY:
            return 'bid'
        else:
            return 'ask'


class OrderType(Enum):
    MARKET = 'market'
    LIMIT = 'limit'

    def __repr__(self):
        return self.name


class OrderStatus(Enum):
    OPEN = 'open'
    CLOSED = 'closed'
    CANCELED = 'canceled'

    def __repr__(self):
        return self.name


class TxType(Enum):
    DEPOSIT = 'deposit'
    WITHDRAWAL = 'withdrawal'

    def __repr__(self):
        return self.name


class TxStatus(Enum):
    OK = 'ok'
    FAILED = 'failed'
    CANCELED = 'canceled'
    PENDING = 'pending'

    def __repr__(self):
        return self.name


class Timestamped:
    def __post_init__(self):
        if self.timestamp is None:
            maya_dt = maya.now()
            self.timestamp = maya_dt.epoch
        else:
            maya_dt = maya.MayaDT(self.timestamp)
        if self.datetime is None:
            self.datetime = maya_dt.datetime()
        self.iso8601 = maya_dt.iso8601()


@dataclass
class Ticker(Timestamped):
    market: Market
    bid: Money
    ask: Money
    last: Money
    open: Optional[Money] = field(repr=False)
    high: Optional[Money] = field(repr=False)
    low: Optional[Money] = field(repr=False)
    close: Optional[Money] = field(repr=False)
    change: Optional[Money] = field(repr=False)
    percentage: Optional[Decimal] = field(repr=False)
    average: Optional[Money] = field(repr=False)
    vwap: Optional[Money] = field(repr=False)
    info: Any = field(default=None, repr=False)
    timestamp: int = field(default=None, repr=False)
    datetime: dt = field(default=None, repr=False)
    iso8601: str = field(default=None, init=False)


@dataclass
class Balance:
    total: Money
    free: Optional[Money]
    used: Optional[Money]
    info: Any = field(default=None, repr=False)


@dataclass
class Trade(Timestamped):
    id: Optional[str]
    market: Market
    type: Optional[OrderType]
    side: Optional[Side]
    amount: Money
    price: Money
    cost: Optional[Money] = field(repr=False)
    fee: Optional[Money] = field(repr=False)
    info: Any = field(default=None, repr=False)
    timestamp: int = field(default=None, repr=False)
    datetime: dt = field(default=None, repr=False)
    iso8601: str = field(default=None, init=False)

    @classmethod
    def create_default(cls, market: Market, amount: Decimal, price: Decimal=None, timestamp: int=None) -> 'Trade':
        return cls(
            id=None,
            market=market,
            type=None,
            side=None,
            amount=Money(amount, market.base),
            price=Money(price, market.quote),
            cost=None,
            fee=None,
            info=None,
            timestamp=timestamp,
        )


@dataclass
class Order(Timestamped):
    id: Optional[str]
    market: Market
    type: OrderType
    side: Side
    status: Optional[OrderStatus]
    amount: Money
    remaining: Optional[Money] = field(repr=False)
    cost: Optional[Money] = field(repr=False)
    filled: Optional[Money] = field(repr=False)
    fee: Optional[Money] = field(repr=False)
    price: Optional[Money] = field(repr=False)
    info: Any = field(default=None, repr=False)
    timestamp: int = field(default=None, repr=False)
    datetime: dt = field(default=None, repr=False)
    iso8601: str = field(default=None, init=False)

    @classmethod
    def create_default(cls, market: Market, order_type: OrderType, side: Side,
                       amount: Decimal, price: Decimal=None, timestamp: int=None) -> 'Order':
        return cls(
            id=None,
            market=market,
            type=order_type,
            side=side,
            status=None,
            amount=Money(amount, market.base),
            remaining=None,
            filled=None,
            cost=None,
            fee=None,
            price=price,
            info=None,
            timestamp=timestamp,
        )


@dataclass
class OrderBookEntry:
    price: Money
    amount: Money


OrderBookSide = List[OrderBookEntry]


@dataclass
class OrderBook(Timestamped):
    market: Market
    bids: OrderBookSide = field(repr=False)
    asks: OrderBookSide = field(repr=False)
    info: Any = field(default=None, repr=False)
    timestamp: int = field(default=None, repr=False)
    datetime: dt = field(default=None, repr=False)
    iso8601: str = field(default=None, init=False)

    def __repr__(self):
        name = self.__class__.__qualname__
        return f'{name}(' + ', '.join([
            f'market={self.market}',
            f'bids={len(self.bids)}',
            f'asks={len(self.asks)}',
            f'iso8601={self.iso8601}',
        ]) + ')'

    def get_book_side(self, side: Side) -> OrderBookSide:
        return self.bids if side == Side.BUY else self.asks

    @cached_property
    def volume_bid(self):
        """Get bid volume from order book."""
        return sum(o.amount for o in self.bids)

    @cached_property
    def volume_ask(self):
        """Get ask volume from order book."""
        return sum(o.amount for o in self.asks)

    @cached_property
    def volume(self) -> Money:
        """Get total volume from order book."""
        return self.volume_bid + self.volume_ask

    @cached_property
    def volume_details(self) -> Tuple[Money, Money, Money]:
        """Get volume from order book, returns (total, bid, ask)."""
        volume_bid = self.volume_bid
        volume_ask = self.volume_ask
        volume_total = self.volume
        return volume_total, volume_bid, volume_ask

    def _quote_book_price(self, side: Side, amount: Decimal) -> Money:
        # Flip sides, for a buy quotation we need to quote the sell book (asks)
        side = Side.SELL if side == side.BUY else Side.BUY
        order_book_side = self.get_book_side(side)
        remaining = amount
        quote = 0
        if not order_book_side:
            raise OrderBookEmpty(f'{side.value.title()} order book is empty!')
        for order in order_book_side:
            remaining -= order.amount.amount
            quote = order.price
            if remaining < 0:
                break
        if remaining > 0:
            raise QuotationError(f'Total amount on {side} order book is not enough to cover quote')
        return quote

    def quote_price(self, side: Side, amount: Number=0) -> Money:
        """Quote price for an amount from a side of the order book."""
        amount = parse_money(amount, self.market.base)
        return self._quote_book_price(side, amount)

    def quote_buy_price(self, amount: Number=0) -> Money:
        """Quote a buy price for an amount from the order book."""
        return self.quote_price(Side.BUY, amount)

    def quote_sell_price(self, amount: Number=0) -> Money:
        """Quote a sell price for an amount from the order book."""
        return self.quote_price(Side.SELL, amount)

    def quote_spread_details(self, amount: Number=0) -> Tuple[Money, Money, Money]:
        """Quote spread details (bid, ask, spread) for an amount from the order book."""
        bid = self.quote_sell_price(amount)
        ask = self.quote_buy_price(amount)
        spread = ask - bid
        return bid, ask, spread

    def quote_spread(self, amount: Number=0) -> Money:
        """Quote the spread for an amount from the order book."""
        bid, ask, spread = self.quote_spread_details(amount)
        return spread

    @cached_property
    def spread_details(self) -> Tuple[Money, Money, Money]:
        """Get the spread details (bid, ask, spread) for an amount from the order book."""
        return self.quote_spread_details()

    @cached_property
    def spread(self) -> Money:
        """Get the spread from order book."""
        return self.quote_spread()

    @cached_property
    def bid_price(self) -> Money:
        """Get the bid price from order book."""
        return self.quote_buy_price()

    @cached_property
    def ask_price(self) -> Money:
        """Get the ask price from order book."""
        return self.quote_sell_price()

    @cached_property
    def vw_price(self) -> Money:
        """Get the volume-weighted price from order book."""
        volume_total, volume_bid, volume_ask = self.volume_details
        bid, ask, spread = self.spread_details
        if volume_total:
            sum_prod = volume_bid.amount * bid.amount + volume_ask.amount * ask.amount
            vw_price = Money(sum_prod / volume_total.amount, self.market.quote)
        else:
            vw_price = None
        return vw_price


@dataclass
class Transaction(Timestamped):
    id: Optional[Union[str, int]]
    type: TxType
    currency: str
    amount: Money
    status: Optional[TxStatus]
    address: Optional[str]
    tx_hash: Optional[str] = field(repr=False)
    fee: Optional[Money] = field(repr=False)
    info: Any = field(default=None, repr=False)
    timestamp: int = field(default=None, repr=False)
    datetime: dt = field(default=None, repr=False)
    iso8601: str = field(default=None, init=False)

    @classmethod
    def create_default(cls, tx_type: TxType, currency: str, amount: Decimal, address: str,
                       timestamp=timestamp) -> 'Transaction':
        return cls(
            id=None,
            type=tx_type,
            currency=currency,
            amount=Money(amount, currency),
            status=None,
            address=address,
            tx_hash=None,
            fee=None,
            info=None,
            timestamp=timestamp,
        )


Withdrawal = Transaction
Deposit = Transaction
