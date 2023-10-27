import json
from flask import Flask, request, jsonify, make_response

app = Flask(__name__)
#reading given sample data from json file and creating a python dictionary from it using json.load() function
def load_sample_data(filename):
    try:
        with open(filename, 'r') as file:
            sample_data = json.load(file)
        return sample_data
    except FileNotFoundError:
        print("File cannot be found.")
    except json.JSONDecodeError:
        print("JSON data cannot be loaded successfully.")
    return None
#this function constructs a JSON response with getting data and status_code parameters
def build_response(data, status_code):
    response = {
        "page": data.get("page", 1),
        "page_size": data.get("page_size", 10),
        "count": data.get("count", 0),
        "results": data.get("results", [])
    }
    return jsonify(response), status_code
#calculating  a subset of values according to the given page and page size
def get_paginated_data(unique_values, page, page_size):
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size

    if start_idx >= len(unique_values):
        return None, make_response(jsonify({"error": "Page out of range"}), 400)

    paginated_data = unique_values[start_idx:end_idx]

    response = {
        "page": page,
        "page_size": page_size,
        "count": len(unique_values),
        "results": paginated_data
    }

    return response, 200
#filtering unique_values based on the provided criterias
def apply_filters(unique_values, filters):
    for col, filter_value in filters.items():
        if col in colon_structure:
            col_row = colon_structure[col]
            if col_row == "ENUM":
                unique_values = [value for value in unique_values if filter_value in value]
            elif col_row == "NUMERIC":
                if isinstance(filter_value, list) and len(filter_value) == 2:
                    unique_values = [value for value in unique_values if filter_value[0] <= value <= filter_value[1]]
                elif isinstance(filter_value, (int, float)):
                    unique_values = [value for value in unique_values if value == filter_value]
            elif col_row == "FREE FORM":
                unique_values = [value for value in unique_values if filter_value in value]
    return unique_values
#ordering the unique_values based on the provided ordering criterias
def apply_ordering(unique_values, ordering):
    for order in ordering:
        for col, direction in order.items():
            if col in colon_structure and direction in ["ASC", "DESC"]:
                reverse = (direction == "DESC")
                unique_values.sort(reverse=reverse)
    return unique_values

colon_structure = {
    "main.uploaded_variation": "ENUM",
    "main.existing_variation": "ENUM",
    "main.symbol": "ENUM",
    "main.af_vcf": "NUMERIC",
    "main.dp": "NUMERIC",
    "details2.dann_score": "NUMERIC",
    "links.mondo": "FREE FORM",
    "links.pheno pubmed": "FREE FORM",
    "details2.provean": "FREE FORM",
}
#handling both GET and POST requests and passing them to the '/assignment/query' URL
@app.route('/assignment/query', methods=['GET', 'POST'])
def query_data():
    if request.method == 'GET':
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        sample_data = load_sample_data('sample_data.json')

        if sample_data is None:
            return make_response(jsonify({"error": "Failed to load data."}), 500)

        unique_values = sample_data.get("main.uploaded_variation", {}).get("unique_values", [])

        if page <= 0 or page_size <= 0:
            response = {
                "error": "Invalid page or page_size values"
            }
            return make_response(jsonify(response), 400)

        # Applying filters and ordering
        filters = request.args.to_dict()
        unique_values = apply_filters(unique_values, filters)

        response, status_code = get_paginated_data(unique_values, page, page_size)

        if status_code == 200:
            return build_response(response, status_code)
        else:
            return response
    elif request.method == 'POST':
        request_data = request.get_json()
        filters = request_data.get("filters", {})
        ordering = request_data.get("ordering", [])

        sample_data = load_sample_data('sample_data.json')

        if sample_data is None:
            return make_response(jsonify({"error": "Failed to load data."}), 500)

        unique_values = sample_data.get("main.uploaded_variation", {}).get("unique_values", [])


        unique_values = apply_filters(unique_values, filters)
        unique_values = apply_ordering(unique_values, ordering)

        # Paging
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 10))

        response, status_code = get_paginated_data(unique_values, page, page_size)

        if status_code == 200:
            return build_response(response, status_code)
        else:
            return response

if __name__ == '__main__':
    app.run(debug=True)