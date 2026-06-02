from tkinter.messagebox import showerror, showinfo, askyesno
from tkinter import *
from tkinter import ttk
from models import Permission

root = Tk()
root.geometry("1200x1080")

columns = ['ID','Роль','Метод','Ссылка']

state = {
    "canvas_edit": None,
    "canvas_add": None,
    "tree": None
}

def update_table():
    state["tree"].delete(*state['tree'].get_children())
    for p in Permission.select():
        state['tree'].insert('', END, values=[p.id, p.role_id, p.method, p.url])

def add():
    if state["canvas_add"]:
        state["canvas_add"].destroy()
        state["canvas_add"] = None
    state["canvas_add"] = Canvas(root,width=300,height=250,bg="white")
    if state["canvas_edit"]:
        state["canvas_add"].place(x=state["tree"].winfo_width()+110,y=340)
    else:
        state["canvas_add"].place(x=state["tree"].winfo_width()+110,y=50)

    def kill():
        state["canvas_add"].destroy()
        state["canvas_add"] = None

    Button(state["canvas_add"],text='X',background='red',command=kill).place(x=285,y=0)
    Label(state["canvas_add"], text="Добавление",bg="white").place(x=0,y=0)

    frame_edit = Frame(state["canvas_add"],bg="white",width=300,height=200)
    frame_edit.place(x=3,y=20)

    Label(frame_edit,text="Роль",bg="white").place(x=5,y=0)
    entry_role = ttk.Combobox(frame_edit,values=[1,2,3,4,5,6],state='readonly')
    entry_role.place(x=5,y=20)

    Label(frame_edit,text="Метод",bg="white").place(x=5,y=60)
    entry_method = ttk.Combobox(frame_edit,values=['GET','POST','PUT',"PATCH",'DELETE'],state='readonly')
    entry_method.place(x=5,y=80)

    Label(frame_edit,text="Ссылка",bg="white").place(x=5,y=120)
    entry_url = Entry(frame_edit,bg="white",width=40)
    entry_url.place(x=5,y=140)

    def update():
        try:
            role = entry_role.get()
            method = entry_method.get()
            url = entry_url.get()
            Permission.create(role_id=role, method=method, url=url)
            showinfo("Добавление", "Успешно создано")
            update_table()
            state["canvas_add"].destroy()
            state["canvas_add"] = None
        except:
            showerror('Добавление','Роль не выбрана')

    Button(frame_edit,text='Сохранить',background='white',command=update).place(x=5,y=180)

Button(text='Добавить',background='white',command=add).place(x=50,y=20)

state['tree'] = ttk.Treeview(columns=columns,show='headings')
state['tree'].place(x=50,y=50)

scroll = ttk.Scrollbar(orient="vertical",command=state['tree'].yview)
scroll.place(x=652,y=50)

state['tree'].heading('ID',text='ID')
state['tree'].column('ID',width=100)
state['tree'].heading('Роль',text='Роль')
state['tree'].column('Роль',width=100)
state['tree'].heading('Метод',text="Метод")
state['tree'].column('Метод',width=100)
state['tree'].heading('Ссылка',text='Ссылка')
state['tree'].column('Ссылка',width=300)

for p in Permission.select():
    state['tree'].insert('',END,values=[p,p.role_id,p.method,p.url])


def select_item(event):
    selected_items = state['tree'].selection()

    if not selected_items:
        if state["canvas_edit"]:
            state["canvas_edit"].destroy()
            state["canvas_edit"] = None
        return

    select_data = state['tree'].item(selected_items[0])['values']

    if not state["canvas_edit"]:
        state["canvas_edit"] = Canvas(root,width=300,height=250,bg="white")
        if state["canvas_add"]:
            state["canvas_edit"].place(x= state['tree'].winfo_width()+110,y=340)
        else:
            state["canvas_edit"].place(x= state['tree'].winfo_width() + 110, y=50)

    def kill():
        state["canvas_edit"].destroy()
        state["canvas_edit"] = None

    Button(state["canvas_edit"],text='X',background='red',command=kill).place(x=285,y=0)
    Label(state["canvas_edit"], text="Редактирование",bg="white").place(x=0,y=0)

    frame_edit = Frame(state["canvas_edit"],bg="white",width=300,height=200)
    frame_edit.place(x=3,y=20)

    Label(frame_edit,text="Роль",bg="white").place(x=5,y=0)
    entry_role = ttk.Combobox(frame_edit,values=[1,2,3,4,5,6],state='readonly')
    entry_role.place(x=5,y=20)
    entry_role.set(select_data[1])

    Label(frame_edit,text="Метод",bg="white").place(x=5,y=60)
    entry_method = ttk.Combobox(frame_edit,values=['GET','POST','PUT','DELETE'],state='readonly')
    entry_method.place(x=5,y=80)
    entry_method.set(select_data[2])

    link_default = StringVar(value=select_data[3])
    Label(frame_edit,text="Ссылка",bg="white").place(x=5,y=120)
    entry_url = Entry(frame_edit,bg="white",width=40,textvariable=link_default)
    entry_url.place(x=5,y=140)

    def update():
        try:
            role = entry_role.get()
            method = entry_method.get()
            url = entry_url.get()
            Permission.update(role_id=role,method=method,url=url).where(Permission.id==select_data[0]).execute()
            showinfo("Добавление", "Успешно создано")
            update_table()
            state["canvas_edit"].destroy()
            state["canvas_edit"] = None
        except:
            showerror('Добавление','Роль не выбрана')

    Button(frame_edit,text='Сохранить',background='white',command=update).place(x=5,y=180)

def delete(event):
    item =  state['tree'].selection()
    if not item:
        showinfo('Удаление',"Вы не выбрали элемента для удаления")
        return

    if askyesno('Удаление','Вы действительно хотите удалить выбранный элемент?'):
        Permission.delete().where(Permission.id ==  state['tree'].item(item,'values')[0]).execute()
        showinfo('Удаление','Успешно')
        state["canvas_edit"].destroy()
        state["canvas_edit"] = None
        update_table()

state['tree'].bind('<<TreeviewSelect>>',select_item)
state['tree'].bind('<Button-3>',delete)


if __name__ == "__main__":
    root.mainloop()