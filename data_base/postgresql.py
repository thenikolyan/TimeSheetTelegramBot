import pandas as pd
import psycopg2
from sshtunnel import SSHTunnelForwarder

from data_base import schema
from config import *

def server(ip, flag):
    server = SSHTunnelForwarder(
        (ip, 1222),
        ssh_username=ssh_un,
        ssh_password=ssh_pw,
        remote_bind_address=(host, 5432))
    server.start()
    print("server connected")

    params = {
        'database': db_name,
        'user': db_un,
        'password': db_pw,
        'host': host,
        'port': server.local_bind_port
    }

    connection = psycopg2.connect(**params)
    connection.autocommit = True
    cursor = connection.cursor()
    if flag:
        return connection
    else:
        return cursor


def sql_start():
    global con, cur
    con = server(ip, 1)
    cur = server(ip, 0)

    if con:
        print('Success connection!')
    cur.execute(schema.schema)

    con.commit()
    print('Success creation!')


async def sql_user_add(data):
    cur.execute(f'''
                do $$
                begin 
                    if not exists(select uid from worktime.users where uid = {data["uid"]} ) then 
                        insert into worktime.users (uid, username, date_start) values {tuple(data.values())}; 
                        insert into worktime.category (uid, category) values ({data['uid']}, 'meet'); 
                    end if; 
                end $$;''')


async def sql_user_category_add(data):
    cur.execute((f'''
                do $$
                begin
                    if not exists(select uid from worktime.category where uid = {data['uid']}  and category = '{data['category']}') then
                        insert into worktime.category (uid, category) values {tuple(data.values())};
                    end if;
                end $$;'''))


async def sql_user_category_del(data):
    cur.execute(f"delete from worktime.category where uid = {data['uid']} and category = '{data['category']}' and category != 'meet';")


async def sql_user_category_rename(data):
    cur.execute(f"update worktime.category set category = '{data['new_name']}' where category = '{data['last_name']}' and uid = {data['uid']} and category != 'meet';")


async def sql_entries_add(data):
    cur.execute(
        f"insert into worktime.entries (uid, category, time, date, comment) values {tuple(data.values())}")


async def show_categories(uid):
    return (pd.read_sql(f"select category from worktime.category where uid = {uid} and category != 'meet'", con).to_dict('records'))


async def sql_change_time_of_work(data):
    cur.execute(f"update worktime.users set daily_work_rate = {data['time']} where uid = {data['uid']};")


async def schedule_send():
    return (pd.read_sql(f"select * from worktime.users where username = 'thenikolyan';", con).to_dict('records'))


async def sql_work_sum():
    return (pd.read_sql(f"select uid, daily_work_rate, time from "
                        f"worktime.users left join (select uid, sum(time) as time, date from worktime.entries "
                        f"where current_date = date "
                        f"GROUP by (uid, date)) as all_time using (uid) "
                        f"where daily_work_rate < time and ;", con).to_dict('records'))


async def sql_check_user(uid):
    return (pd.read_sql(f'select true from worktime.users where uid={uid}', con).to_dict('records'))
