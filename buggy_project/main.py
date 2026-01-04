
            from utils import calculate_total


            cart = [
                {'name': '사과', 'price' : 1500, 'quantity' : 5},
                {'name': '바나나', 'price' : 3000, 'quantity' : 2},
            ]


            try:
                total = calculate_total(cart)
                print(f'총 합계 : {total}')
            except TypeError as e:
                print(f'오류가 발생했습니다.: {e}')
            