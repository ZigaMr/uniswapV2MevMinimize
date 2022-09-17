import math
import pandas as pd

def expected_return_fees(token_pool, weth_pool, value, fee=997, pct=1):
    return (value * fee * token_pool / (weth_pool * 1000 + value * fee)) * pct


def calculate_frontrun_return(my_eth, target_eth, token_pool, weth_pool, div=10 ** 18, fee=997, pct=1):
    a1 = expected_return_fees(token_pool, weth_pool, my_eth, fee, pct)
    a2 = expected_return_fees(token_pool - a1, weth_pool + my_eth, target_eth, fee, pct)

    return (
    my_eth / div, expected_return_fees(weth_pool + my_eth + target_eth, token_pool - a2 - a1, a1, fee, pct) / div,
    a2 / div) if div else (
        my_eth, expected_return_fees(weth_pool + my_eth + target_eth, token_pool - a2 - a1, a1, fee, pct), a2)


def binary_search(target_eth, token_pool, weth_pool, out_min, error_margin, upper=5, lower=0, pct=1):
    if upper > lower:
        mid = (upper + lower) / 2
        my_eth, profit_eth, target_tokens = calculate_frontrun_return(mid * 10 ** 18, target_eth,
                                                                      token_pool, weth_pool, False, pct=pct)
        if abs(upper - lower) * 10 ** 18 < error_margin:
            print(upper)
            if target_tokens < out_min:
                return calculate_frontrun_return(lower * 10 ** 18, target_eth, token_pool, weth_pool, False, pct=pct)
            else:
                return my_eth, profit_eth, target_tokens

        if target_tokens < out_min:
            return binary_search(target_eth, token_pool, weth_pool, out_min, error_margin, mid, lower, pct=pct)
        else:
            return binary_search(target_eth, token_pool, weth_pool, out_min, error_margin, upper, mid, pct=pct)
    return False


def optimal_bid(r0, vx):
    return -(1000 / 997) * r0 + 997000 / 5991 * vx + 10 / 5991 * (-179730 * r0 * vx + 9999820270 * vx ** 2) ** (0.5)

def optimal_bid2(aIn, k, aOut):
    return (-997*aIn + math.sqrt((997*aIn)**2 - 4000*(-997*k*aIn/aOut)))/2000


if __name__ == '__main__':
    data = pd.DataFrame(columns=['binary', 'analytical'])
    data['variable'] = range(1, 200)
    data.analytical = data.variable.apply(lambda x: optimal_bid2(10**18, 10**38, x*10**16)-10**19)
    data.binary = data.variable.apply(lambda x: binary_search(10**18, 10*10**18, 10*10**18, x*10**16, 10**10, 100, 0)[0])



