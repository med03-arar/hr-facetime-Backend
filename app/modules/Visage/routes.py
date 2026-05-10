from flask import Blueprint, request, jsonify
from datetime import datetime
from decimal import Decimal
import re

from ...extensions import db
from ...models.Visage import Face
from ...models.user import User
bp = Blueprint("Visage", __name__)