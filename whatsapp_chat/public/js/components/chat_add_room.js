import { create_private_room } from './chat_utils';

export default class ChatAddRoom {
  constructor(opts) {
    this.user = opts.user;
    this.users_list = [...frappe.user.get_emails(), 'Administrator'];
    this.user_email = opts.user_email;
    this.users_list = this.users_list.filter(function (user) {
      return user != opts.user_email;
    });
    this.setup();
  }

  async setup() {
    this.add_room_dialog = new frappe.ui.Dialog({
      title: __('New Chat Room'),
      fields: [

        {
          label: __('Contact Name'),
          fieldname: 'contact_name',
          fieldtype: 'Data',
          reqd: true,
        },
        {
          label: __('Mobile number'),
          fieldname: 'mobile_no',
          description: "Mobile number with country code",
          fieldtype: 'Data',
          reqd: true,
        },
        {
          label: __('User'),
          fieldname: 'email',
          description: "Assign user to chat",
          fieldtype: 'Link',
          options: "User",
          reqd: true,
        },
      ],
      action: {
        primary: {
          label: __('Create'),
          onsubmit: (values) => {
            // let users = this.add_room_dialog.fields_dict.users.get_values();
            // let room_name = values.room_name;
            // if (values.type === 'Direct') {
            //   users = [values.user];
            //   room_name = 'Direct Room';
            // }
            this.handle_room_creation(values.contact_name, values.mobile_no, values.email);
            this.add_room_dialog.hide();
          },
        },
      },
    });
  }

  show() {
    this.add_room_dialog.show();
  }

  async handle_room_creation(contact_name, mobile_no, email) {
    try {
      await create_private_room(contact_name, mobile_no, email);
      this.add_room_dialog.clear();
    } catch (error) {
      //pass
    }
  }
}
