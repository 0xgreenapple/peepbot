
CREATE OR REPLACE FUNCTION peep.check_user_details_guild_ids()
RETURNS TRIGGER AS $$
DECLARE
check_parent_table Integer;
BEGIN
	SELECT Count(*) INTO check_parent_table FROM peep.users
	WHERE user_id = NEW.user_id AND guild_id = NEW.guild_id;
	IF check_parent_table = 0 THEN
	INSERT INTO peep.users(guild_id,user_id)
	VALUES(NEW.guild_id,NEW.user_id);
	END IF;
	RETURN NEW;
END;
$$ language plpgsql;

CREATE OR REPLACE TRIGGER user_details_trigger
BEFORE INSERT ON peep.user_details
FOR EACH ROW EXECUTE FUNCTION peep.check_user_details_guild_ids();


CREATE OR REPLACE FUNCTION peep.check_shop_guild_ids()
RETURNS TRIGGER AS $$
DECLARE
check_parent_table Integer;
BEGIN
	SELECT Count(*) INTO check_parent_table FROM peep.guilds
	WHERE guild_id = NEW.guild_id;
	IF check_parent_table = 0 THEN
	INSERT INTO peep.guilds(guild_id)
	VALUES(NEW.guild_id);
	END IF;
	RETURN NEW;
END;
$$ language plpgsql;

CREATE OR REPLACE TRIGGER insert_shop_guild_ids
BEFORE INSERT ON peep.shop
FOR EACH ROW EXECUTE FUNCTION peep.check_shop_guild_ids();


CREATE OR REPLACE FUNCTION peep.check_user_guild_ids()
RETURNS TRIGGER AS $$
DECLARE
check_guild_ids Integer;
BEGIN
    SELECT Count(*) INTO check_guild_ids FROM peep.Guilds
    WHERE guild_id = NEW.guild_id;
    IF check_guild_ids = 0 THEN
    INSERT INTO peep.Guilds(guild_id)
    VALUES(NEW.guild_id);
    END IF;
    RETURN NEW;
END;
$$ language plpgsql;

CREATE or REPLACE TRIGGER insert_user_guild_ids
BEFORE INSERT ON peep.Users
FOR EACH ROW EXECUTE FUNCTION peep.check_user_guild_ids();


CREATE OR REPLACE FUNCTION peep.check_channels_guild_ids()
RETURNS TRIGGER AS $$
DECLARE
check_guild_ids Integer;
BEGIN
    SELECT Count(*) INTO check_guild_ids FROM peep.Guilds
    WHERE guild_id = NEW.guild_id;
    IF check_guild_ids = 0 THEN
    INSERT INTO peep.Guilds(guild_id)
    VALUES(NEW.guild_id);
    END IF;
    RETURN NEW;
END;
$$ language plpgsql;

CREATE or REPLACE TRIGGER insert_channel_guild_ids
BEFORE INSERT ON peep.Channels
FOR EACH ROW EXECUTE FUNCTION peep.check_channels_guild_ids();


CREATE OR REPLACE FUNCTION peep.check_gallery_guild_ids()
RETURNS TRIGGER AS $$
DECLARE
check_guild_ids Integer;
BEGIN
    SELECT Count(*) INTO check_guild_ids FROM peep.Guilds
    WHERE guild_id = NEW.guild_id AND channel_id = NEW.channel_id;
    IF check_guild_ids = 0 THEN
    INSERT INTO peep.Channels(guild_id,channel_id)
    VALUES(NEW.guild_id,NEW.channel_id);
    END IF;
    RETURN NEW;
END;
$$ language plpgsql;

CREATE or REPLACE TRIGGER insert_Gallery_guild_ids
BEFORE INSERT ON peep.Gallery
FOR EACH ROW EXECUTE FUNCTION peep.check_gallery_guild_ids();



CREATE OR REPLACE FUNCTION peep.check_guild_settings_guild_ids()
RETURNS TRIGGER AS $$
DECLARE
check_guild_ids Integer;
BEGIN
    SELECT Count(*) INTO check_guild_ids FROM peep.Guilds
    WHERE guild_id = NEW.guild_id;
    IF check_guild_ids = 0 THEN
    INSERT INTO peep.Guilds(guild_id)
    VALUES(NEW.guild_id);
    END IF;
    RETURN NEW;
END;
$$ language plpgsql;

CREATE or REPLACE TRIGGER insert_guild_settings_guild_ids
BEFORE INSERT ON peep.guild_settings
FOR EACH ROW EXECUTE FUNCTION peep.check_guild_settings_guild_ids();


CREATE OR REPLACE FUNCTION peep.check_user_inv_guild_ids()
RETURNS TRIGGER AS $$
DECLARE
check_parent_table Integer;
BEGIN
	SELECT Count(*) INTO check_parent_table FROM peep.users
	WHERE user_id = NEW.user_id AND guild_id = NEW.guild_id;
	IF check_parent_table = 0 THEN
	INSERT INTO peep.users(guild_id,user_id)
	VALUES(NEW.guild_id,NEW.user_id);
	END IF;
	RETURN NEW;
END;
$$ language plpgsql;

CREATE OR REPLACE TRIGGER insert_user_inv_guild_id
BEFORE INSERT ON peep.inventory
FOR EACH ROW EXECUTE FUNCTION peep.check_user_inv_guild_ids();