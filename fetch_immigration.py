"""Fetch immigration series: migratory balance, permanent immigrant inflows,
foreign resident stock.

Data caveat documented in README: the 2022-2024 surge in resident permits is
partially driven by extraordinary regularizations (CPLP mobility, declaratory
regime/'manifestacao de interesse' until 2024), so the *stock* of legal
residents jumps even when the *flow* of new arrivals does not match it.
"""
from common import fetch_topic

CODES = {
    '0013179': 'Migratory balance (N.), annual, updated methodology',
    '0006054': 'Permanent immigrants (N.), annual, by sex/age/prior residency (variant A)',
    '0006055': 'Permanent immigrants (N.), annual (variant B)',
    '0006056': 'Permanent immigrants (N.), annual (variant C)',
    '0006057': 'Permanent immigrants (N.), annual (variant D)',
    '0001274': 'Foreign population with legal resident status (N.), by sex, 1980-',
    '0013219': 'Foreign population with legal resident status (N.), by NUTS-2024 and nationality, 2021-',
}

if __name__ == '__main__':
    fetch_topic(CODES)