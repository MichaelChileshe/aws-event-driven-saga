#!/usr/bin/env python3
"""Regenerates docs/architecture.svg + docs/architecture.png using the OFFICIAL AWS Architecture Icons.

The icon pack is not committed (AWS licenses it for diagrams, not redistribution). Download it from
https://aws.amazon.com/architecture/icons/, unzip, then:

    AWS_ICONS_DIR=/path/to/unzipped-icon-package python3 build_architecture.py
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from awsdiag import Diagram, GREY, INK

FLOW, COMP, EVT, XACCT, OK, SF = "#545B64", "#D13212", "#E7157B", "#ED7100", "#1D8102", "#E7157B"
d = Diagram(1800, 1180)

d.text(40, 40, "Nkosi Payments — merchant settlement as a saga, announced with events", 19, "bold")
d.text(40, 64, "Step Functions Standard (saga) + Express (validation)  ·  EventBridge custom bus, archive/replay, "
               "cross-account delivery  ·  Lambda  ·  DynamoDB  ·  SQS  ·  us-east-1", 13, "normal", GREY)

d.group("cloud", 20, 90, 1760, 1075, "AWS Cloud  ·  AWS Organizations")
d.group("account", 40, 130, 1330, 1015, "Nkosi Payments  —  management account")
d.group("account", 1395, 130, 365, 520, "Finance team  —  nkosi-sandbox")


def state(x, y, label, color=FLOW, fill="#FFFFFF", w=190):
    d.raw(f'<rect x="{x}" y="{y}" width="{w}" height="34" rx="6" fill="{fill}" stroke="{color}" stroke-width="1.4"/>')
    d.text(x + w / 2, y + 22, label, 12, "bold", INK if color == FLOW else color, "middle")


# ---------------------------------------------------------------- the saga
d.box(65, 175, 625, 500, SF, fill="#FFF7FB")
d.icon("step_functions", 80, 187, 40)
d.text(128, 203, "Step Functions STANDARD  ·  nkosi-settlement-saga", 13.5, "bold")
d.text(128, 220, "one execution per settlement · execution name = settlement ID (duplicates refused)", 11.5, "normal", GREY)

LX, RX = 100, 450
state(LX, 245, "ReserveFunds")
state(LX, 305, "PostLedgerCredit")
state(LX, 365, "Payout", XACCT, "#FFF4E8")
state(LX, 450, "RecordPayout")
state(LX, 510, "Publish  ‖  Audit  (Parallel)")
state(LX, 570, "MarkCompleted", OK, "#F1F8EE")
for y1, y2 in [(279, 303), (339, 363), (399, 448), (484, 508), (544, 568)]:
    d.line([(LX + 95, y1), (LX + 95, y2)], FLOW)
d.text(LX + 103, 418, "Retry BankTimeout ×3 · 2/4/8 s", 11, "bold", XACCT)
d.text(LX + 103, 434, "pivot: money has left", 11, "normal", GREY)

d.icon("lambda_fn", 312, 361, 42)
d.text(333, 350, "bank gateway", 10.5, "normal", GREY, "middle")

state(RX, 365, "ReverseLedgerCredit", COMP, "#FDF0EF")
state(RX, 425, "ReleaseFunds", COMP, "#FDF0EF")
state(RX, 485, "MarkCompensated", COMP, "#FDF0EF")
state(RX, 545, "PublishCompensated", COMP, "#FDF0EF")
state(RX, 605, "Fail: SettlementCompensated", COMP, "#FBE3E1", w=210)
for y1, y2 in [(399, 423), (459, 483), (519, 543), (579, 603)]:
    d.line([(RX + 95, y1), (RX + 95, y2)], COMP)
d.line([(356, 382), (RX - 2, 382)], COMP, dashed=True)
d.label(372, 372, "Catch", COMP, 10.5)
d.line([(LX + 190, 322), (420, 322), (420, 442), (RX - 2, 442)], COMP, dashed=True)
d.label(424, 318, "Catch", COMP, 10.5)
d.text(RX + 105, 660, "compensation runs in REVERSE order", 11, "bold", COMP, "middle")

# ledger + before inset
d.line([(126, 675), (126, 703)], FLOW)
d.icon("dynamodb", 100, 705, 52)
d.text(162, 722, "DynamoDB  nkosi-settlement-ledger", 12.5, "bold")
d.text(162, 739, "one item per step + reversals", 11.5, "normal", GREY)
d.text(162, 755, "(the measuring instrument)", 11.5, "normal", GREY)

d.box(65, 800, 625, 120, COMP, fill="#FFFFFF")
d.icon("lambda", 82, 822, 48)
d.text(145, 830, "BEFORE: Lambda nkosi-settlement-monolith", 13, "bold", COMP)
d.text(145, 848, "reserve → credit → call bank → (crash) … no retry, no undo", 11.5, "normal", GREY)
d.text(145, 866, "same 20 settlements: 8 PARTIAL, R76,110.00 stranded", 11.5, "bold", COMP)
d.text(145, 884, "(3 of the 8 were only bank timeouts a retry would have fixed)", 11.5, "normal", GREY)

# ---------------------------------------------------------------- events
d.icon("users", 760, 158, 48)
d.text(812, 174, "Card acquiring", 12.5, "bold")
d.text(812, 190, "TransactionReceived", 11.5, "normal", GREY)
d.line([(784, 210), (784, 368)], EVT)

d.icon("eventbridge", 752, 370, 64)
d.text(784, 452, "EventBridge", 12.5, "bold", anchor="middle")
d.text(784, 468, "custom bus nkosi-payments", 11.5, "normal", GREY, "middle")
d.line([(690, 402), (750, 402)], EVT)

d.box(720, 495, 145, 58, "#8C4FFF", fill="#F7F3FF")
d.text(792, 516, "Archive (1 day)", 12, "bold", "#8C4FFF", "middle")
d.text(792, 533, "replays to same bus", 11, "normal", GREY, "middle")
d.line([(784, 476), (784, 494)], "#8C4FFF", dashed=True, arrow=False)

# rules fan-out
d.line([(816, 402), (880, 402)], EVT, arrow=False)
d.line([(880, 230), (880, 710)], EVT, arrow=False)
rules = [
    (230, "nkosi-settlement-feed", "live settlement events"),
    (390, "txn-received-to-validate", "every TransactionReceived"),
    (550, "settlements-to-finance", "SettlementCompleted, not replays"),
    (710, "nkosi-replay-inspect", "replay-name exists"),
]
for y, name, sub in rules:
    d.line([(880, y), (918, y)], EVT)
    d.icon("eb_rule", 920, y - 20, 40)
    d.text(966, y - 4, name, 12, "bold")
    d.text(966, y + 12, sub, 11, "normal", GREY)

# targets
d.line([(1150, 230), (1188, 230)], EVT)
d.icon("sqs_queue", 1190, 208, 44)
d.text(1242, 226, "SQS", 12, "bold")
d.text(1242, 242, "settlement feed", 11, "normal", GREY)

d.line([(1150, 390), (1188, 390)], EVT)
d.icon("step_functions", 1190, 366, 48)
d.text(1246, 385, "Step Functions", 12, "bold")
d.text(1246, 401, "EXPRESS validate", 11, "normal", GREY)
d.line([(1214, 416), (1214, 452)], FLOW)
d.icon("dynamodb", 1190, 454, 48)
d.text(1246, 472, "txn-validations", 12, "bold")
d.text(1246, 488, "180 ✓ · 20 ✗", 11, "normal", GREY)

d.line([(1150, 710), (1188, 710)], EVT)
d.icon("sqs_queue", 1190, 688, 44)
d.text(1242, 706, "SQS", 12, "bold")
d.text(1242, 722, "replay-inspect", 11, "normal", GREY)

# cross-account
d.line([(1150, 550), (1444, 550)], XACCT, width=2.5)
d.icon("iam_role", 1262, 520, 34)
d.text(1279, 578, "role: PutEvents", 10.5, "normal", XACCT, "middle")
d.icon("eb_bus", 1446, 526, 48)
d.text(1470, 596, "nkosi-finance-events", 11, "bold", anchor="middle")
d.text(1470, 612, "policy: allow Nkosi", 10.5, "normal", GREY, "middle")
d.line([(1496, 550), (1546, 550)], EVT)
d.icon("eb_rule", 1548, 530, 40)
d.line([(1590, 550), (1648, 550)], EVT)
d.icon("sqs_queue", 1650, 528, 44)
d.text(1672, 596, "finance-inbox", 11, "bold", anchor="middle")
d.text(1580, 420, "Each side controls its half:", 11.5, "bold", INK, "middle")
d.text(1580, 437, "the bus policy allows the account,", 11, "normal", GREY, "middle")
d.text(1580, 453, "the sender's role allows PutEvents", 11, "normal", GREY, "middle")

# ---------------------------------------------------------------- measured + legend
bx, by = 1395, 675
d.box(bx, by, 365, 300, "#D5DBDB", fill="#fff", dashed=False)
d.text(bx + 14, by + 26, "Measured", 13.5, "bold")
lines = [
    ("Partial settlements: 8 → 0", OK, "bold"),
    ("Money stranded: R76,110.00 → R0.00", OK, "bold"),
    ("Bank timeouts rescued by retry: 3 of 3", INK, "normal"),
    ("Payout rejections compensated: 5 of 5", INK, "normal"),
    ("Duplicate settlement: refused by AWS", INK, "normal"),
    ("Express: 200 validated, 20 caught", INK, "normal"),
    ("Cross-account: delivered to finance", INK, "normal"),
    ("Replay: 24 events in 71 s", INK, "normal"),
    ("  → inspection rule only", INK, "normal"),
    ("  → live feed 0, finance 0", INK, "normal"),
]
for i, (t, c, w) in enumerate(lines):
    d.text(bx + 14, by + 52 + i * 24, t, 12, w, c)

lx, ly = 1395, 995
d.raw(f'<rect x="{lx}" y="{ly}" width="365" height="130" rx="4" fill="#fff" stroke="#D5DBDB"/>')
d.text(lx + 12, ly + 22, "Legend", 13, "bold")
d.line([(lx + 12, ly + 44), (lx + 58, ly + 44)], FLOW)
d.text(lx + 66, ly + 48, "saga forward path", 11.5)
d.line([(lx + 12, ly + 66), (lx + 58, ly + 66)], COMP, dashed=True)
d.text(lx + 66, ly + 70, "Catch → compensation", 11.5)
d.line([(lx + 12, ly + 88), (lx + 58, ly + 88)], EVT)
d.text(lx + 66, ly + 92, "events (publish / route / deliver)", 11.5)
d.line([(lx + 12, ly + 110), (lx + 58, ly + 110)], XACCT, width=2.5)
d.text(lx + 66, ly + 114, "cross-account delivery", 11.5)

here = os.path.dirname(os.path.abspath(__file__))
d.save(os.path.join(here, "..", "architecture.svg"), os.path.join(here, "..", "architecture.png"))
print("wrote docs/architecture.svg and docs/architecture.png")
