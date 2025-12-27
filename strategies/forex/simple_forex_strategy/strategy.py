from zipline.api import order, record, symbol

def initialize(context):
    context.asset = symbol('EURUSD')
    context.i = 0

def handle_data(context, data):
    context.i += 1
    if context.i < 100: # Only trade for a few days to avoid excessive data requirements
        order(context.asset, 1)
    record(EURUSD=data.current(context.asset, 'price'))

