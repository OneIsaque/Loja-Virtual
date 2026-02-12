from flask import Flask, render_template, redirect, url_for, session, flash
from decimal import Decimal
import os

app = Flask(__name__)
app.secret_key = os.urandom(24)

# Banco de dados em memória
produtos = [
    {"id": 1, "nome": "Camisa", "preco": 50.0, "estoque": 10},
    {"id": 2, "nome": "Calça", "preco": 120.0, "estoque": 5},
    {"id": 3, "nome": "Tênis", "preco": 200.0, "estoque": 8},
    {"id": 4, "nome": "Boné", "preco": 30.0, "estoque": 15},
    {"id": 5, "nome": "Jaqueta", "preco": 150.0, "estoque": 7}
]

# Funções auxiliares
def get_cart():
    return session.setdefault("carrinho", [])

def save_cart(cart):
    session["carrinho"] = cart

def total_calculado(cart):
    total = sum(Decimal(str(item["preco"])) * item["quantidade"] for item in cart)
    total_qtd = sum(item["quantidade"] for item in cart)
    return float(total), total_qtd

# Rotas
@app.route("/")
def home():
    return render_template("home.html")

@app.route("/menu")
def menu():
    return render_template("menu.html", produtos=produtos)

@app.route("/cart")
def cart_ver():
    cart = get_cart()
    total, total_qtd = total_calculado(cart)
    return render_template("cart.html", carrinho=cart, total=total, total_qtd=total_qtd)

@app.route("/add/<int:id>")
def add_item(id):
    cart = get_cart()
    produto = next((p for p in produtos if p["id"] == id), None)

    # produto não existe
    if produto is None:
        flash("Produto não encontrado.", "error")
        return redirect(url_for("menu"))

    # sem estoque
    if produto["estoque"] <= 0:
        flash(f"Sem estoque para {produto['nome']}.", "error")
        return redirect(url_for("menu"))

    # adicionar ao carrinho (ou incrementar)
    for item in cart:
        if item["id"] == id:
            item["quantidade"] += 1
            break
    else:
        cart.append({
            "id": produto["id"],
            "nome": produto["nome"],
            "preco": produto["preco"],
            "quantidade": 1
        })

    produto["estoque"] -= 1
    save_cart(cart)
    flash(f"{produto['nome']} adicionado ao carrinho.", "success")
    return redirect(url_for("cart_ver"))

@app.route("/add_mais/<int:item_id>")
def add_mais(item_id):
    cart = get_cart()
    produto = next((p for p in produtos if p["id"] == item_id), None)

    if produto is None:
        flash("Produto não encontrado.", "error")
        return redirect(url_for("cart_ver"))

    if produto["estoque"] <= 0:
        flash(f"Sem mais unidades de {produto['nome']} em estoque.", "error")
        return redirect(url_for("cart_ver"))

    for item in cart:
        if item["id"] == item_id:
            item["quantidade"] += 1
            produto["estoque"] -= 1
            save_cart(cart)
            flash(f"Mais uma unidade de {produto['nome']} adicionada.", "success")
            return redirect(url_for("cart_ver"))

    # se não estava no carrinho, redireciona para rota de adicionar
    return redirect(url_for("add_item", id=item_id))

@app.route("/remove_one/<int:item_id>")
def remove_one(item_id):
    cart = get_cart()
    for item in list(cart):  # iterar sobre cópia para evitar problemas ao remover
        if item["id"] == item_id:
            # devolver 1 unidade ao estoque
            produto = next((p for p in produtos if p["id"] == item_id), None)
            if produto:
                produto["estoque"] += 1

            if item["quantidade"] > 1:
                item["quantidade"] -= 1
            else:
                cart.remove(item)
            save_cart(cart)
            flash(f"Uma unidade de {item['nome']} removida do carrinho.", "success")
            return redirect(url_for("cart_ver"))

    flash("Item não encontrado no carrinho.", "error")
    return redirect(url_for("cart_ver"))

@app.route("/remove_all/<int:item_id>")
def remove_all(item_id):
    cart = get_cart()
    for item in list(cart):
        if item["id"] == item_id:
            produto = next((p for p in produtos if p["id"] == item_id), None)
            if produto:
                produto["estoque"] += item["quantidade"]
            cart.remove(item)
            save_cart(cart)
            flash(f"Todas as unidades de {item['nome']} removidas do carrinho.", "success")
            return redirect(url_for("cart_ver"))

    flash("Item não encontrado no carrinho.", "error")
    return redirect(url_for("cart_ver"))

@app.route("/remove_similar/<string:char>")
def remove_similar(char):
    cart = get_cart()
    key = char.lower()
    novos_itens = []
    removed_any = False

    for item in cart:
        if key in item["nome"].lower():
            produto = next((p for p in produtos if p["id"] == item["id"]), None)
            if produto:
                produto["estoque"] += item["quantidade"]
            removed_any = True
        else:
            novos_itens.append(item)

    save_cart(novos_itens)
    if removed_any:
        flash(f"Itens contendo '{char}' removidos do carrinho.", "success")
    else:
        flash(f"Nenhum item contendo '{char}' no carrinho.", "error")
    return redirect(url_for("cart_ver"))


@app.route("/checkout")
def checkout():
    cart = get_cart()
    total, _ = total_calculado(cart)
    # checkout finaliza a compra: não devolve ao estoque
    cart.clear()
    save_cart(cart)
    flash("Compra finalizada. Obrigado!", "success")
    return render_template("checkout.html", total=total)


if __name__ == "__main__":
    app.run(debug=True)
