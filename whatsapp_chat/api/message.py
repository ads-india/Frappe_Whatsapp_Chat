import frappe
import mimetypes



@frappe.whitelist()
def get_all(room: str, user_no: str):
    """Get all the messages of a particular room

    Args:
        room (str): Room's name.

    """
    return frappe.db.sql("""
        SELECT creation,
        case
            when `to` <> '' then `to`
            else
            'Administrator'
        end as sender_user_no,
        case
            when content_type = 'text' then message
            else attach
        end as content
        from `tabWhatsApp Message` where (`to` = %(user_no)s or `from` = %(user_no)s)
        AND message_type <> 'Template'
        order by creation asc
    """, {"user_no": user_no}, as_dict=True)


@frappe.whitelist()
def mark_as_read(room):
    doc = frappe.get_doc("WhatsApp Contact", room)
    doc.is_read = 1
    doc.save()

    return "ok"



@frappe.whitelist()
def send(content, user, room, user_no, attachment=None):
    content_type = "text"
    if attachment:
        file_type = mimetypes.guess_type(content)[0]
        if file_type in ["image/apng","image/avif","image/gif","image/jpeg","image/png","image/svg","image/webp"]:
            content_type = 'image'
        elif file_type in ["application/pdf", "application/vnd.ms-powerpoint", "application/msword", "application/vnd.ms-excel", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "application/vnd.openxmlformats-officedocument.presentationml.presentation", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]:
            content_type = "document"
        elif file_type in ["audio/aac", "audio/mp4", "audio/mpeg", "audio/amr", "audio/ogg"]:
            content_type = 'audio'
        elif file_type in ["video/mp4", "video/3gp"]:
            content_type = "video"

        frappe.get_doc({
            "doctype": "WhatsApp Message",
            "to": user_no,
            "type": "Outgoing",
            "attach": content,
            "content_type": content_type
        }).save()
    else:
        frappe.get_doc({
            "doctype": "WhatsApp Message",
            "to": user_no,
            "type": "Outgoing",
            "message": content,
            "content_type": content_type
        }).save()

    return "ok"


def last_message(doc, method):
    if doc.type == 'Outgoing':
        mobile_no = doc.to
        sender_user_no = doc.owner
    else:
        mobile_no = doc.get("from")
        sender_user_no = mobile_no

    message_content = doc.message or doc.attach

    room_name = frappe.db.get_value("WhatsApp Contact", filters={"mobile_no": mobile_no})
    if room_name:
        chat_doc = frappe.get_doc("WhatsApp Contact", room_name)
        chat_doc.last_message = message_content
        chat_doc.is_read = 0
        chat_doc.save(ignore_permissions=True)
    else:
        new_contact = frappe.get_doc(
            {
                "doctype": "WhatsApp Contact",
                "mobile_no": mobile_no,
                "last_message": message_content,
                "contact_name": mobile_no,
                "is_read": 0,
            }
        ).save(ignore_permissions=True)
        room_name = new_contact.name
        new_room_profile = {
            "room": new_contact.name,
            "room_name": new_contact.contact_name,
            "last_message": new_contact.last_message,
            "last_date": new_contact.modified,
            "is_read": new_contact.is_read,
            "type": "Direct",
            "mobile_no": new_contact.mobile_no,
        }
        frappe.publish_realtime(event="new_room_creation", message=new_room_profile, after_commit=True)

    sender_name = ""
    if doc.type == 'Outgoing':
        sender_name = frappe.db.get_value("User", doc.owner, "full_name")
    else:
        sender_name = frappe.db.get_value("WhatsApp Contact", room_name, "contact_name") or mobile_no

    message_for_publish = {
        "content": message_content,
        "creation": doc.creation,
        "room": room_name,
        "sender_user_no": sender_user_no,
        "user": sender_name
    }

    frappe.publish_realtime(
        event=room_name, message=message_for_publish, after_commit=True
    )
    frappe.publish_realtime(
        event="latest_chat_updates", message=message_for_publish, after_commit=True
    )

    # For CRM integration, publish to 'whatsapp_message' topic
    if doc.get("reference_doctype") and doc.get("reference_name"):
        crm_payload = {
            "reference_doctype": doc.reference_doctype,
            "reference_name": doc.reference_name,
        }
        frappe.publish_realtime(
            event="whatsapp_message", message=crm_payload, after_commit=True
        )

    return "ok"
