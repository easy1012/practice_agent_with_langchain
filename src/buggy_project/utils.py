

def calculate_total(cart_items):
    total_price = 0
    for item in cart_items:
        total_price += item['price'] * item['quantity']
    
    return total_price

