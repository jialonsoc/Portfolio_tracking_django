from django.db import models

# Create your models here.
class Asset(models.Model):
    """activo invertible i"""
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name
    
class Portfolio(models.Model):
    "es el portfolio, con el valor inicial V0 en t = 0"
    name = models.CharField(max_length=100, unique=True)
    initial_value = models.DecimalField(max_digits=20, decimal_places=2)
    start_date = models.DateField() #aqui es donde pongo los t = 0,1,2, etc
    
    def __str__(self):
        return self.name

class Price(models.Model):
    """se puede ver como p_{i,t}: precio del activo i en el tiempo t"""
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='prices')
    date = models.DateField(db_index=True)
    value = models.DecimalField(max_digits=20, decimal_places=8)

    class Meta:
        unique_together = ('asset', 'date')

    def __str__(self):
        return f"{self.asset.name} @ {self.date}: {self.value}"

class InitialWeight(models.Model):
    "peso inicial del activo i en el portfolio se puede ver como w_{i,0}"
    portfolio = models.ForeignKey(Portfolio,on_delete=models.CASCADE, related_name='initial_weights')
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name='initial_weights')
    weight = models.DecimalField(max_digits=12, decimal_places=8)

    class Meta:
        unique_together = ('portfolio', 'asset')

    def __str__(self):
        return f"{self.portfolio.name} / {self.asset.name}: {self.weight}"

class Holding(models.Model):
    "cuanto tenemos de cada activo en el portfolio en el tiempo t se puede ver como c_{i,t}"
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE, related_name="holdings")
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE, related_name="holdings")
    quantity = models.DecimalField(max_digits=28, decimal_places=12)


    class Meta:
        unique_together = ('portfolio', 'asset')
    
    def __str__(self):
        return f"{self.portfolio.name} / {self.asset.name}: {self.quantity}"
