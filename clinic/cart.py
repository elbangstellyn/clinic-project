from .models import Drug

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, drug_id, quantity=1, override_quantity=False):
        drug_id = str(drug_id)
        if drug_id not in self.cart:
            self.cart[drug_id] = {'quantity': 0, 'price': str(Drug.objects.get(id=drug_id).price)}
        if override_quantity:
            self.cart[drug_id]['quantity'] = quantity
        else:
            self.cart[drug_id]['quantity'] += quantity
        self.save()

    def save(self):
        self.session.modified = True

    def __iter__(self):
        drug_ids = self.cart.keys()
        drugs = Drug.objects.filter(id__in=drug_ids)
        drug_dict = {str(drug.id): drug for drug in drugs}
        for item_id, item_data in self.cart.items():
            drug = drug_dict.get(item_id)
            if drug:
                yield {
                    'drug': drug,
                    'quantity': item_data['quantity'],
                    'price': float(item_data['price']),
                    'total_price': float(item_data['price']) * item_data['quantity']
                }

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(float(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        del self.session['cart']
        self.save()