import time


def wait_redis_channel_upd(redis_store, channel, empty_msg_limit=10):

    pubsub = redis_store.pubsub()
    pubsub.psubscribe(channel)

    CHECK = True

    empty_msg = 0

    while CHECK:
        message = pubsub.get_message()

        if message:
            CHECK = False

        else:
            empty_msg += 1

        if empty_msg == empty_msg_limit:
            print("Limit exceeded!")
            return

        time.sleep(0.2)


def wait_redis_update(
    redis_store, channel, expected_kv, num_expected_updates, empty_msg_limit=10
):

    pubsub = redis_store.pubsub()
    pubsub.psubscribe(channel)

    CHECK = True
    keys_updated = {}
    num_updated = 0
    empty_msg = 0

    while CHECK:
        message = pubsub.get_message()
        # print(message)
        if message and message["pattern"] == str.encode(channel):
            data = message["data"].decode("utf-8")
            if "-" in data:
                key, _ = data.split("-")
                keys_updated[int(key)] = data
                num_updated += 1

                if num_updated >= num_expected_updates:
                    CHECK = False

        else:
            empty_msg += 1

        if empty_msg == empty_msg_limit:
            print(
                "One of the values hasn't been updated: {}".format(
                    set(expected_kv.keys()) - set(keys_updated.keys())
                )
            )
            return

        time.sleep(0.2)

        # time.sleep(0.2)
    return keys_updated
