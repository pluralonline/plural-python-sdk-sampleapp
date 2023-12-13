from flask import Flask, jsonify, render_template, request, redirect
import uuid
import json
from pinelabs.src.Pinelabs import Pinelabs

app = Flask(__name__)

@app.route("/payment")
def payment():
    return render_template('Index.html', txn_id=uuid.uuid4().hex)

@app.route("/payment/hash")
def hash():
    return render_template('Hash.html')

@app.route("/payment/fetch")
def fetch():
    return render_template('Fetch.html')

@app.route("/createOrder/Response" , methods=['GET', 'POST'])
def orderResponse():
    form_data = request.form.to_dict(flat=False)
    print(form_data)
    if form_data:
        received_form_data = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}
        try:
            # Extract single values from arrays
            single_values = {k: v if not isinstance(v, list) else v[0] for k, v in received_form_data.items()}
            parsed_json = json.loads(json.dumps(single_values))
            return parsed_json
            # return render_template('OrderResponse.html', data=parsed_json)
        except Exception as e:
            return render_template('OrderResponse.html', data="Error")
    received_json = request.get_json()
    parsed_json = json.loads(received_json)
    return parsed_json

@app.route("/payment/emi")
def emi():
    return render_template('Emi.html')

@app.route("/payment/submit", methods=["POST"])
def payment_create():
    data = request.form
    txn_data = {
        "txn_id": data.get("txn_id"),
        "callback": data.get("callback_url"),
        "amount_in_paisa": data.get("amount_in_paisa"),
    }
    customer_data = {
        "email_id": data.get("email"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "mobile_no": data.get("phone"),
        "customer_id": data.get("customer_id"),
    }
    billing_data = {
        "address1": data.get("address1"),
        "address2": data.get("address2"),
        "address3": data.get("address3"),
        "pincode": data.get("billing_pincode"),
        "city": data.get("city"),
        "state": data.get("state"),
        "country": data.get("country"),
    }
    shipping_data = {
        "first_name": data.get("shipping_firstname"),
        "last_name": data.get("shipping_lastname"),
        "mobile_no": data.get("shipping_phone"),
        "address1": data.get("shipping_address1"),
        "address2": data.get("shipping_address2"),
        "address3": data.get("shipping_address3"),
        "pincode": data.get("shipping_pincode"),
        "city": data.get("shipping_city"),
        "state": data.get("shipping_state"),
        "country": data.get("shipping_country"),
    }
    udf_data = {
        "udf_field_1": data.get("udf1"),
        "udf_field_2": data.get("udf2"),
        "udf_field_3": data.get("udf3"),
        "udf_field_4": data.get("udf4"),
        "udf_field_5": data.get("udf5"),
    }

    modes = data.getlist("payment_mode[]")

    payment_mode = {
        "netbanking": "netbanking" in modes,
        "cards": "card" in modes,
        "emi": "emi" in modes,
        "upi": "upi" in modes,
        "cardless_emi": "cardless_emi" in modes,
        "wallet": "wallet" in modes,
        "debit_emi": "debit_emi" in modes,
        "prebooking": "prebooking" in modes,
        "bnpl": "bnpl" in modes,
        "paybypoints": "paybypoints" in modes,
    }
    product_details = None
    if data.get("products") is not None and data.get("products") != "":
        try:
                product_details = json.loads(data.get("products"))
        except json.JSONDecodeError as e:
               print("Error decoding JSON:", e)

    pinelabs = Pinelabs(data.get("merchantId"), data.get("access_code"), data.get("secret"), data.get("pg_mode") == "true")
    orderCreateResponse = pinelabs.payment.create(txn_data, customer_data, billing_data, shipping_data, udf_data, payment_mode, product_details)
    print(orderCreateResponse)
    return redirect(orderCreateResponse["redirect_url"])


@app.route("/payment/fetch/status", methods=["POST"])
def payment_fetch():
    data = request.form
    pinelabs = Pinelabs(data.get("merchantId"), data.get("access_code"), data.get("secret"), data.get("pg_mode") == "true")
    orderFetchResponse = pinelabs.payment.fetch(data.get("txn_id"))
    json_formatted_str = json.dumps(orderFetchResponse, indent=2)
    return render_template('Fetch.html', res = json_formatted_str)

@app.route("/payment/emis", methods=["POST"])
def payment_emi():
    data = request.form
    pinelabs = Pinelabs(data.get("merchantId"), data.get("access_code"), data.get("secret"), data.get("pg_mode") == "true")
    txn_data = {
        "amount_in_paisa": data.get("product_amount"),
    }
    product_details=None
    try:
        product_details = json.loads(data.get("products"))
    except json.JSONDecodeError as e:
           print("Error decoding JSON:", e)
    try:
        orderEmiResponse = pinelabs.emi.calculate(txn_data, product_details)
    except Exception as e:
           return render_template('Emi.html', res = e)
    json_formatted_str = json.dumps(orderEmiResponse, indent=2)
    return render_template('Emi.html', res = json_formatted_str)


@app.route("/payment/verify", methods=["POST"])
def payment_hash():
  try:
      data = request.form
      data2 = request.form.get('products')
      products = json.loads(data2) 
      secret=None
      if 'ppc_DIA_SECRET' in products:
          secret=products.get('ppc_DIA_SECRET')
          del products['ppc_DIA_SECRET']
      if 'ppc_DIA_SECRET_TYPE' in products:
          del products['ppc_DIA_SECRET_TYPE']
      if 'dia_secret' in products:
          secret=products.get('dia_secret')
          del products['dia_secret']
      if 'dia_secret_type' in products:
          del products['dia_secret_type']
      pinelabs = Pinelabs(data.get("merchantId"), data.get("access_code"), data.get("secret"), data.get("pg_mode") == "true")
      isVerified = pinelabs.hash.verify(secret, products)
      print(isVerified)
      return jsonify(isVerified), 200
  except Exception as e:
      isVerified=False
      return jsonify(isVerified), 200
