from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from wtforms import FloatField, IntegerField, SelectField
from wtforms.validators import NumberRange

class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    submit = SubmitField("Register")

class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class ProfileForm(FlaskForm):
    annual_income = FloatField("Annual Income", validators=[DataRequired(), NumberRange(min=1)])
    credit_score = IntegerField("Credit Score", validators=[DataRequired(), NumberRange(min=0, max=999)])
    employment_type = SelectField(
        "Employment Type",
        choices=[("employed", "Employed"), ("self-employed", "Self-employed")],
        validators=[DataRequired()]
    )
    monthly_expenses = FloatField("Monthly Expenses", validators=[DataRequired(), NumberRange(min=0)])
    monthly_debts = FloatField("Monthly Debts", validators=[DataRequired(), NumberRange(min=0)])
    submit = SubmitField("Save Profile")

# New form for the mortgage calculator.
class MortgageCalculatorForm(FlaskForm):
    amount = FloatField(
        "Loan Amount",
        validators=[DataRequired(), NumberRange(min=1)]
    )

    rate = FloatField(
        "Interest Rate",
        validators=[DataRequired(), NumberRange(min=0)]
    )

    term_years = IntegerField(
        "Mortgage Term in Years",
        validators=[DataRequired(), NumberRange(min=1, max=100)]
    )

    submit = SubmitField("Calculate Mortgage")