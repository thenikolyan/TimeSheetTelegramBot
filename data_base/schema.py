schema = '''create schema if not exists worktime;

            create table if not exists worktime.status(
                status integer primary key,
                description text);
            
            do $$
            begin
                if not exists(select * from worktime.status where status = 0 ) then
                    insert into worktime.status (status, description) values (0, 'user');
                end if;
            end $$;
            
            
            create table if not exists worktime.users(
                uid bigint primary key,
                username text not null,
                status integer default 0,
                daily_work_rate integer default 7200,
                date_start date not null,
                date_end date default '2023-01-01');
            
            create table if not exists worktime.category(
                uid bigint not null,
                category text not null,
                PRIMARY KEY(uid, category)
                );
            
            create table if not exists worktime.entries(
                id SERIAL primary key,
                uid bigint not null,
                category text not null,
                time integer not null,
                date date not null,
                comment text default 'без комментариев'
                );
            
            
            ALTER table worktime.entries
            drop constraint if exists FKentries_users;
            
            ALTER table worktime.entries
            ADD CONSTRAINT FKentries_users 
            FOREIGN KEY (uid) REFERENCES worktime.users (uid);
            
            
            ALTER table worktime.entries
            drop constraint if exists FKentries_category;
            
            ALTER table worktime.entries
            ADD CONSTRAINT  FKentries_category
            FOREIGN KEY (uid, category) REFERENCES worktime.category (uid, category) on delete cascade on update cascade;
            
            ALTER table worktime.users
            drop constraint if exists FKusers_status;
            
            ALTER table worktime.users
            ADD CONSTRAINT FKusers_status 
            FOREIGN KEY (status) REFERENCES worktime.status (status);
            
            
            CREATE SEQUENCE if not exists table_id_seq;
            
            ALTER TABLE worktime.entries 
                ALTER COLUMN id 
                    SET DEFAULT NEXTVAL('table_id_seq');
            '''
