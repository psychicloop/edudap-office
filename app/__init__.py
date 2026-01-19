

{% extends 'base.html' %}
{% block content %}
<h3>My Expenses</h3>

{{ url_for(

  <div class="col-md-2">
    <label class="form-label">Amount</label>
    <input name="amount" type="number" step="0.01" class="form-control" required>
  </div>

  <div class="col-md-2">
    <label class="form-label">Currency</label>
    <input name="currency" value="INR" class="form-control">
  </div>

  <div class="col-md-3">
    <label class="form-label">Category</label>
    <input name="category" class="form-control">
  </div>

  <div class="col-md-3">
    <label class="form-label">Caption</label>
    <input name="caption" class="form-control">
  </div>

  <div class="col-md-3">
    <label class="form-label">Attachment</label>
    <input name="attachment" type="file" class="form-control">
  </div>

  <div class="col-auto">
    <button class="btn btn-primary">Submit</button>
  </div>
</form>

<hr>

<div class="table-responsive">
  <table class="table table-sm table-striped align-middle">
    <thead>
      <tr>
        <th>When</th>
        <th>Amount</th>
        <th>Caption</th>
        <th>Status</th>
        <th>File</th>
      </tr>
    </thead>
    <tbody>
      {% for e in records %}
        <tr>
          <td>{{ e.submitted_at }}</td>
          <td>{{ e.currency }} {{ '%.2f' % e.amount }}</td>
          <td>{{ e.caption }}</td>
          <td>{{ e.status }}</td>
          <td>
            {% if e.file_path %}
              <!-- file_path like: uploads/expenses/xxx.pdf -->
              /{{ e.file_path }}
                📎 Open
              </a>
            {% endif %}
          </td>
        </tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}

