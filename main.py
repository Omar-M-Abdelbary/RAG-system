from flask import Flask, request, render_template
from Rag import retrieve  

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def query_rag():
    if request.method == "POST":
        query = request.form.get("query")
        results = retrieve(query, top_n=3)
        response = "<br>".join(results) 
        return render_template("rag.html", query=query, response=response)
    
    return render_template("rag.html", query="", response="")

if __name__ == "__main__":
    app.run(debug=True)