from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    # Base price, can be overridden by variants
    base_price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    product = models.ForeignKey(
        Product, related_name='variants', on_delete=models.CASCADE)
    size = models.CharField(max_length=10, blank=True, null=True)
    color = models.CharField(max_length=50, blank=True, null=True)
    # Specific price for this variant
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.name} - {self.color} - {self.size}"


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"Image for {self.product.name}"
