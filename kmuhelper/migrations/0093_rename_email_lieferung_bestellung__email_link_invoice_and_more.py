# Generated by Django 4.1.6 on 2023-02-07 16:39

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("kmuhelper", "0092_rename_rabatt_bestellungskosten_discount_and_more"),
    ]

    operations = [
        migrations.RenameField(
            model_name="bestellung",
            old_name="email_lieferung",
            new_name="email_link_shipped",
        ),
        migrations.RenameField(
            model_name="bestellung",
            old_name="email_rechnung",
            new_name="email_link_invoice",
        ),
        migrations.RenameField(
            model_name="bestellung",
            old_name="ausgelagert",
            new_name="is_removed_from_stock",
        ),
        migrations.RenameField(
            model_name="bestellung",
            old_name="produkte",
            new_name="products",
        ),
        migrations.RenameField(
            model_name="lieferung",
            old_name="eingelagert",
            new_name="is_added_to_stock",
        ),
        migrations.RenameField(
            model_name="lieferung",
            old_name="produkte",
            new_name="products",
        ),
        migrations.RenameField(
            model_name="produkt",
            old_name="aktion_von",
            new_name="sale_from",
        ),
        migrations.RenameField(
            model_name="produkt",
            old_name="aktion_preis",
            new_name="sale_price",
        ),
        migrations.RenameField(
            model_name="produkt",
            old_name="aktion_bis",
            new_name="sale_to",
        ),
        migrations.RenameField(
            model_name="produktkategorie",
            old_name="uebergeordnete_kategorie",
            new_name="parent_category",
        ),
        migrations.RenameField(
            model_name="zahlungsempfaenger",
            old_name="firmenname",
            new_name="name",
        ),
        migrations.RenameField(
            model_name="zahlungsempfaenger",
            old_name="firmenuid",
            new_name="swiss_uid",
        ),
        migrations.RenameField(
            model_name="produkt",
            old_name="kategorien",
            new_name="categories",
        ),
        migrations.AlterField(
            model_name="produkt",
            name="categories",
            field=models.ManyToManyField(
                related_name="products",
                through="kmuhelper.ProduktProduktkategorieVerbindung",
                to="kmuhelper.produktkategorie",
                verbose_name="Kategorie",
            ),
        ),
    ]
