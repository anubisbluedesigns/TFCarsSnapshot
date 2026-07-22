-- Auto-generated from SQLAlchemy models targeting Snowflake dialect.
-- Uses explicit SEQUENCEs (not AUTOINCREMENT) so SQLAlchemy's ORM can
-- fetch generated primary keys via SELECT seq.NEXTVAL before insert.

CREATE SEQUENCE reprice_policy_id_seq;

CREATE SEQUENCE stores_id_seq;

CREATE SEQUENCE users_id_seq;

CREATE SEQUENCE age_band_config_id_seq;

CREATE SEQUENCE bucket_color_map_id_seq;

CREATE SEQUENCE gross_heatmap_config_id_seq;

CREATE SEQUENCE report_titles_id_seq;

CREATE SEQUENCE status_color_map_id_seq;

CREATE SEQUENCE status_options_id_seq;

CREATE SEQUENCE store_goals_id_seq;

CREATE SEQUENCE user_store_scope_id_seq;

CREATE SEQUENCE vehicles_id_seq;

CREATE SEQUENCE price_history_id_seq;

CREATE SEQUENCE store_transfers_id_seq;

CREATE SEQUENCE unwind_events_id_seq;

CREATE TABLE reprice_policy (
	id INTEGER NOT NULL DEFAULT reprice_policy_id_seq.nextval, 
	price_rank INTEGER NOT NULL, 
	day_threshold INTEGER NOT NULL, 
	plan_label VARCHAR NOT NULL, 
	guidance_text VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_reprice_policy UNIQUE (price_rank, day_threshold)
);

CREATE TABLE stores (
	id INTEGER NOT NULL DEFAULT stores_id_seq.nextval, 
	slug VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	offers_new BOOLEAN, 
	offers_used BOOLEAN, 
	stock_prefix VARCHAR, 
	PRIMARY KEY (id), 
	UNIQUE (slug)
);

CREATE TABLE users (
	id INTEGER NOT NULL DEFAULT users_id_seq.nextval, 
	email VARCHAR NOT NULL, 
	name VARCHAR NOT NULL, 
	role VARCHAR NOT NULL, 
	is_active BOOLEAN, 
	PRIMARY KEY (id), 
	UNIQUE (email)
);

CREATE TABLE age_band_config (
	id INTEGER NOT NULL DEFAULT age_band_config_id_seq.nextval, 
	store_id INTEGER, 
	min_days INTEGER NOT NULL, 
	max_days INTEGER, 
	color_hex VARCHAR NOT NULL, 
	sort_order INTEGER, 
	PRIMARY KEY (id), 
	FOREIGN KEY(store_id) REFERENCES stores (id)
);

CREATE TABLE bucket_color_map (
	id INTEGER NOT NULL DEFAULT bucket_color_map_id_seq.nextval, 
	store_id INTEGER NOT NULL, 
	bucket_value VARCHAR NOT NULL, 
	color_hex VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_bucket_color UNIQUE (store_id, bucket_value), 
	FOREIGN KEY(store_id) REFERENCES stores (id)
);

CREATE TABLE gross_heatmap_config (
	id INTEGER NOT NULL DEFAULT gross_heatmap_config_id_seq.nextval, 
	store_id INTEGER, 
	low_threshold FLOAT NOT NULL, 
	high_threshold FLOAT NOT NULL, 
	low_color VARCHAR NOT NULL, 
	mid_color VARCHAR NOT NULL, 
	high_color VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(store_id) REFERENCES stores (id)
);

CREATE TABLE report_titles (
	id INTEGER NOT NULL DEFAULT report_titles_id_seq.nextval, 
	store_id INTEGER NOT NULL, 
	month VARCHAR NOT NULL, 
	title VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_report_title UNIQUE (store_id, month), 
	FOREIGN KEY(store_id) REFERENCES stores (id)
);

CREATE TABLE status_color_map (
	id INTEGER NOT NULL DEFAULT status_color_map_id_seq.nextval, 
	store_id INTEGER NOT NULL, 
	store_type VARCHAR NOT NULL, 
	status_value VARCHAR NOT NULL, 
	color_hex VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_status_color UNIQUE (store_id, store_type, status_value), 
	FOREIGN KEY(store_id) REFERENCES stores (id)
);

CREATE TABLE status_options (
	id INTEGER NOT NULL DEFAULT status_options_id_seq.nextval, 
	store_id INTEGER NOT NULL, 
	store_type VARCHAR NOT NULL, 
	value VARCHAR NOT NULL, 
	sort_order INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_status_option UNIQUE (store_id, store_type, value), 
	FOREIGN KEY(store_id) REFERENCES stores (id)
);

CREATE TABLE store_goals (
	id INTEGER NOT NULL DEFAULT store_goals_id_seq.nextval, 
	store_id INTEGER NOT NULL, 
	store_type VARCHAR NOT NULL, 
	year INTEGER NOT NULL, 
	quarter INTEGER NOT NULL, 
	map_value FLOAT, 
	par_value FLOAT, 
	target_value FLOAT, 
	PRIMARY KEY (id), 
	FOREIGN KEY(store_id) REFERENCES stores (id)
);

CREATE TABLE user_store_scope (
	id INTEGER NOT NULL DEFAULT user_store_scope_id_seq.nextval, 
	user_id INTEGER NOT NULL, 
	store_id INTEGER NOT NULL, 
	store_type VARCHAR, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_user_store_scope UNIQUE (user_id, store_id, store_type), 
	FOREIGN KEY(user_id) REFERENCES users (id), 
	FOREIGN KEY(store_id) REFERENCES stores (id)
);

CREATE TABLE vehicles (
	id INTEGER NOT NULL DEFAULT vehicles_id_seq.nextval, 
	stock_number VARCHAR, 
	vin_tail VARCHAR, 
	originating_store_id INTEGER NOT NULL, 
	current_store_id INTEGER NOT NULL, 
	store_type VARCHAR NOT NULL, 
	year INTEGER, 
	make VARCHAR, 
	model VARCHAR, 
	trim_details VARCHAR, 
	mileage INTEGER, 
	price_rank INTEGER, 
	status VARCHAR NOT NULL, 
	bucket VARCHAR NOT NULL, 
	price FLOAT, 
	cost FLOAT, 
	sold_price FLOAT, 
	sold_cost FLOAT, 
	sold_date DATE, 
	reserved BOOLEAN, 
	reserved_sales_rep VARCHAR, 
	reserved_guest_name VARCHAR, 
	unwound BOOLEAN, 
	tag_otd_special BOOLEAN, 
	inventory_date DATE, 
	created_at datetime, 
	updated_at datetime, 
	updated_by VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(originating_store_id) REFERENCES stores (id), 
	FOREIGN KEY(current_store_id) REFERENCES stores (id)
);

CREATE TABLE price_history (
	id INTEGER NOT NULL DEFAULT price_history_id_seq.nextval, 
	vehicle_id INTEGER NOT NULL, 
	old_price FLOAT, 
	new_price FLOAT, 
	changed_at datetime, 
	changed_by VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(vehicle_id) REFERENCES vehicles (id)
);

CREATE TABLE store_transfers (
	id INTEGER NOT NULL DEFAULT store_transfers_id_seq.nextval, 
	vehicle_id INTEGER NOT NULL, 
	from_store_id INTEGER NOT NULL, 
	to_store_id INTEGER NOT NULL, 
	transferred_at datetime, 
	transferred_by VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(vehicle_id) REFERENCES vehicles (id), 
	FOREIGN KEY(from_store_id) REFERENCES stores (id), 
	FOREIGN KEY(to_store_id) REFERENCES stores (id)
);

CREATE TABLE unwind_events (
	id INTEGER NOT NULL DEFAULT unwind_events_id_seq.nextval, 
	vehicle_id INTEGER NOT NULL, 
	unwound_at datetime, 
	prior_sold_price FLOAT, 
	unwound_by VARCHAR, 
	PRIMARY KEY (id), 
	FOREIGN KEY(vehicle_id) REFERENCES vehicles (id)
);
