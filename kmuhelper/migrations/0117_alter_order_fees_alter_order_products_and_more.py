# Generated by Django 5.2 on 2025-04-08 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("kmuhelper", "0116_add_woocommerceid_indexes"),
    ]

    operations = [
        migrations.AlterField(
            model_name="order",
            name="fees",
            field=models.ManyToManyField(
                through="kmuhelper.OrderFee",
                through_fields=("order", "linked_fee"),
                to="kmuhelper.fee",
            ),
        ),
        migrations.AlterField(
            model_name="order",
            name="products",
            field=models.ManyToManyField(
                through="kmuhelper.OrderItem",
                through_fields=("order", "linked_product"),
                to="kmuhelper.product",
            ),
        ),
        migrations.AlterField(
            model_name="product",
            name="categories",
            field=models.ManyToManyField(
                related_name="products",
                through="kmuhelper.ProductProductCategoryConnection",
                through_fields=("product", "category"),
                to="kmuhelper.productcategory",
                verbose_name="Kategorien",
            ),
        ),
        migrations.AlterField(
            model_name="supply",
            name="products",
            field=models.ManyToManyField(
                through="kmuhelper.SupplyItem",
                through_fields=("supply", "product"),
                to="kmuhelper.product",
            ),
        ),
    ]
