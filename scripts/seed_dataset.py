import os
import sys

# Ensure app is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal, engine, Base
from app.domain.models.core import TestCaseModel, SuccessSpecificationModel, ExecutionTraceModel, TraceStepModel
from app.domain.enums import ScenarioType
from app.services.trace_generator import SyntheticTraceGenerator

# Base test case definitions
TEST_CASES_DATA = [
    # ORDER_MANAGEMENT
    {
        "type": "ORDER_MANAGEMENT", "desc": "Cancel order 101",
        "intent": "cancel_order", "entities": {"order_id": "101"}, "op": "cancel_order", "state": {"status": "cancelled"}
    },
    {
        "type": "ORDER_MANAGEMENT", "desc": "Update delivery address for order 102",
        "intent": "update_address", "entities": {"order_id": "102"}, "op": "update_order_address", "state": {"address_updated": True}
    },
    {
        "type": "ORDER_MANAGEMENT", "desc": "Check order status for order 103",
        "intent": "check_status", "entities": {"order_id": "103"}, "op": "get_order_status", "state": {}
    },
    {
        "type": "ORDER_MANAGEMENT", "desc": "Initiate return for order 104",
        "intent": "return_order", "entities": {"order_id": "104"}, "op": "initiate_return", "state": {"return_initiated": True}
    },
    {
        "type": "ORDER_MANAGEMENT", "desc": "Cancel order 105",
        "intent": "cancel_order", "entities": {"order_id": "105"}, "op": "cancel_order", "state": {"status": "cancelled"}
    },

    # ACCOUNT_MANAGEMENT
    {
        "type": "ACCOUNT_MANAGEMENT", "desc": "Update account email",
        "intent": "update_email", "entities": {"account_id": "A1"}, "op": "update_account", "state": {"email_updated": True}
    },
    {
        "type": "ACCOUNT_MANAGEMENT", "desc": "Reset password preference",
        "intent": "reset_password", "entities": {"account_id": "A2"}, "op": "send_reset_link", "state": {"link_sent": True}
    },
    {
        "type": "ACCOUNT_MANAGEMENT", "desc": "Change notification settings",
        "intent": "update_notifications", "entities": {"account_id": "A3"}, "op": "update_settings", "state": {"notifications_enabled": False}
    },
    {
        "type": "ACCOUNT_MANAGEMENT", "desc": "Delete account",
        "intent": "delete_account", "entities": {"account_id": "A4"}, "op": "delete_account", "state": {"deleted": True}
    },
    {
        "type": "ACCOUNT_MANAGEMENT", "desc": "Update phone number",
        "intent": "update_phone", "entities": {"account_id": "A5"}, "op": "update_account", "state": {"phone_updated": True}
    },

    # BOOKING_MANAGEMENT
    {
        "type": "BOOKING_MANAGEMENT", "desc": "Cancel booking B1",
        "intent": "cancel_booking", "entities": {"booking_id": "B1"}, "op": "cancel_booking", "state": {"status": "cancelled"}
    },
    {
        "type": "BOOKING_MANAGEMENT", "desc": "Modify booking dates B2",
        "intent": "modify_booking", "entities": {"booking_id": "B2"}, "op": "update_booking", "state": {"dates_modified": True}
    },
    {
        "type": "BOOKING_MANAGEMENT", "desc": "Confirm reservation B3",
        "intent": "confirm_booking", "entities": {"booking_id": "B3"}, "op": "confirm_reservation", "state": {"confirmed": True}
    },
    {
        "type": "BOOKING_MANAGEMENT", "desc": "Add guest to booking B4",
        "intent": "add_guest", "entities": {"booking_id": "B4"}, "op": "update_booking", "state": {"guest_added": True}
    },
    {
        "type": "BOOKING_MANAGEMENT", "desc": "Cancel booking B5",
        "intent": "cancel_booking", "entities": {"booking_id": "B5"}, "op": "cancel_booking", "state": {"status": "cancelled"}
    },

    # PAYMENT_REFUND
    {
        "type": "PAYMENT_REFUND", "desc": "Initiate refund for payment P1",
        "intent": "initiate_refund", "entities": {"payment_id": "P1"}, "op": "process_refund", "state": {"refunded": True}
    },
    {
        "type": "PAYMENT_REFUND", "desc": "Check payment status P2",
        "intent": "check_payment", "entities": {"payment_id": "P2"}, "op": "get_payment_status", "state": {}
    },
    {
        "type": "PAYMENT_REFUND", "desc": "Process cancellation refund P3",
        "intent": "process_refund", "entities": {"payment_id": "P3"}, "op": "process_refund", "state": {"refunded": True}
    },
    {
        "type": "PAYMENT_REFUND", "desc": "Retry failed payment P4",
        "intent": "retry_payment", "entities": {"payment_id": "P4"}, "op": "retry_transaction", "state": {"payment_successful": True}
    },
    {
        "type": "PAYMENT_REFUND", "desc": "Initiate partial refund P5",
        "intent": "initiate_refund", "entities": {"payment_id": "P5"}, "op": "process_refund", "state": {"refunded": True}
    },

    # INFORMATION_RETRIEVAL
    {
        "type": "INFORMATION_RETRIEVAL", "desc": "Retrieve account status A1",
        "intent": "get_account", "entities": {"account_id": "A1"}, "op": "fetch_account", "state": {}
    },
    {
        "type": "INFORMATION_RETRIEVAL", "desc": "Retrieve booking details B1",
        "intent": "get_booking", "entities": {"booking_id": "B1"}, "op": "fetch_booking", "state": {}
    },
    {
        "type": "INFORMATION_RETRIEVAL", "desc": "Retrieve order info 101",
        "intent": "get_order", "entities": {"order_id": "101"}, "op": "fetch_order", "state": {}
    },
    {
        "type": "INFORMATION_RETRIEVAL", "desc": "Get product details",
        "intent": "get_product", "entities": {"product_id": "PRD1"}, "op": "fetch_product", "state": {}
    },
    {
        "type": "INFORMATION_RETRIEVAL", "desc": "Get store hours",
        "intent": "get_store", "entities": {"store_id": "S1"}, "op": "fetch_store", "state": {}
    },
]

def seed_database():
    db = SessionLocal()
    
    # Simple idempotent protection: do not seed if test cases already exist.
    if db.query(TestCaseModel).count() > 0:
        print("Dataset already seeded.")
        db.close()
        return

    print("Seeding database...")
    generator = SyntheticTraceGenerator(seed=42)
    
    for tc_data in TEST_CASES_DATA:
        # Create Success Specification
        spec = SuccessSpecificationModel(
            required_intent=tc_data["intent"],
            required_entities=tc_data["entities"],
            required_operations=[{"operation": tc_data["op"], "must_succeed": True}],
            required_final_state=tc_data["state"]
        )
        
        # Create Test Case
        tc = TestCaseModel(
            task_type=tc_data["type"],
            task_description=tc_data["desc"],
            scenario_parameters=tc_data["entities"],
            success_specification=spec
        )
        db.add(tc)
        db.commit()
        db.refresh(tc)
        
        # Select 5 varied scenarios for each test case to generate ~125 traces
        scenarios = [
            ScenarioType.SUCCESS,
            ScenarioType.REQUIRED_OPERATION_FAILURE,
            ScenarioType.WRONG_ENTITY,
            ScenarioType.FALSE_SUCCESS_RESPONSE,
            ScenarioType.TRUTHFUL_FAILURE_RESPONSE
        ]
        
        # Throw in a timeout or partial completion on some
        if int(tc_data["entities"].get("order_id", "0").replace("A","0").replace("B","0").replace("P","0").replace("S","0").replace("PRD","0")) % 2 == 0:
             scenarios[1] = ScenarioType.TIMEOUT
             scenarios[2] = ScenarioType.RETRY_THEN_SUCCESS
        
        for sc in scenarios:
            trace = generator.generate(tc, sc)
            db.add(trace)
    
    db.commit()
    db.close()
    print("Database seeded successfully with ~25 test cases and ~125 traces.")

if __name__ == "__main__":
    seed_database()
