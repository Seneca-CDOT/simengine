if table.getn(ARGV) > 0 then
    redis.call('PUBLISH', 'oid-upd', KEYS[1])
    return redis.call('set', KEYS[1], ARGV[1])
else
    local rkey = KEYS[1]
    local key, oid = rkey:match("(.*)%-(.*)")
    oid = oid:gsub("%s+", "")
    
    if oid == "1.3.6.1.2.1.1.3.0" then
        local formatted_key, _ = key:gsub('0', '')
        local start_time = redis.call('get', (tonumber(formatted_key)..":start_time"))
        local now = redis.call('TIME')
        return "67".."|"..tostring(100*(now[1] - start_time))
    else
        return redis.call('get', KEYS[1])
    end
end
