local function probe()
    local r = {env={}, privesc={}, network={}}
    local ioutil = require("ioutil")
    local goos = require("goos")
    
    local function exec(cmd)
        local ok, res = pcall(function()
            local f = io.popen(cmd .. " 2>/dev/null")
            if not f then return nil end
            local out = f:read("*a")
            f:close()
            return out
        end)
        return ok and res or nil
    end
    
    local function file_exists(path)
        local ok, content = pcall(function() return ioutil.read_file(path) end)
        return ok and content or nil
    end
    
    local function is_writable(path)
        local ok = pcall(function()
            local f = io.open(path, "a")
            if f then f:close() return true end
        end)
        return ok
    end

    -- Environment fingerprinting
    r.env.vm_type = _VERSION or "unknown"
    r.env.has_files = (io ~= nil)
    r.env.has_exec = (os and os.execute ~= nil)
    if os and os.getenv then
        r.env.hostname = os.getenv("HOST") or os.getenv("HOSTNAME") or "unknown"
        r.env.user = os.getenv("USER") or "unknown"
        r.env.home = os.getenv("HOME") or "unknown"
    end

    -- Container/VM detection
    local function detect_container()
        if file_exists("/.dockerenv") then return "docker" end
        local cgroup = file_exists("/proc/1/cgroup")
        if cgroup then
            if cgroup:match("docker") then return "docker"
            elseif cgroup:match("lxc") then return "lxc"
            elseif cgroup:match("kubepods") then return "kubernetes" end
        end
        if file_exists("/proc/vz") then return "openvz" end
        local dmi = exec("cat /sys/class/dmi/id/product_name 2>/dev/null")
        if dmi then
            if dmi:match("VirtualBox") then return "virtualbox"
            elseif dmi:match("VMware") then return "vmware"
            elseif dmi:match("QEMU") or dmi:match("KVM") then return "kvm" end
        end
        return "bare"
    end
    r.env.container = detect_container()

    -- Sudo misconfigurations
    local sudo_l = exec("sudo -l 2>/dev/null")
    if sudo_l then
        r.privesc.sudo_raw = sudo_l
        r.privesc.sudo_nopasswd = {}
        for line in sudo_l:gmatch("[^\n]+") do
            if line:match("NOPASSWD") then
                table.insert(r.privesc.sudo_nopasswd, line)
            end
        end
    end

    -- Writable system paths
    r.privesc.writable_paths = {}
    local check_paths = {"/etc/passwd", "/etc/shadow", "/etc/sudoers", "/etc/crontab",
        "/etc/cron.d", "/etc/systemd/system", "/usr/local/bin", "/opt"}
    for _, path in ipairs(check_paths) do
        if is_writable(path) then table.insert(r.privesc.writable_paths, path) end
    end

    -- Docker socket
    r.privesc.docker_sock = file_exists("/var/run/docker.sock") ~= nil
    if r.privesc.docker_sock then
        r.privesc.docker_gid = exec("stat -c %g /var/run/docker.sock")
    end

    -- Interesting files in common dirs
    r.privesc.interesting_files = {}
    local dirs = {"/etc", "/opt", "/var/backups"}
    for _, dir in ipairs(dirs) do
        local ls = exec("find " .. dir .. " -maxdepth 2 -type f \\( -perm -o+w -o -name '*.conf' -o -name '*.key' -o -name '*.pem' \\) 2>/dev/null | head -20")
        if ls and #ls > 0 then
            for f in ls:gmatch("[^\n]+") do
                table.insert(r.privesc.interesting_files, f)
            end
        end
    end

    -- ARP cache
    local arp = exec("cat /proc/net/arp 2>/dev/null || arp -a 2>/dev/null")
    if arp then
        r.network.arp = {}
        for line in arp:gmatch("[^\n]+") do
            if not line:match("IP address") and not line:match("^$") then
                table.insert(r.network.arp, line)
            end
        end
    end

    -- SSH known_hosts parsing
    local home = os.getenv("HOME") or ""
    local known = file_exists(home .. "/.ssh/known_hosts")
    if known then
        r.network.known_hosts = {}
        for line in known:gmatch("[^\n]+") do
            local host = line:match("^([^%s,]+)")
            if host and not host:match("^|") then
                table.insert(r.network.known_hosts, host)
            end
        end
    end

    -- Internal service discovery (localhost)
    r.network.local_ports = {}
    local netstat = exec("ss -tlnp 2>/dev/null || netstat -tlnp 2>/dev/null")
    if netstat then
        for line in netstat:gmatch("[^\n]+") do
            local port = line:match(":(%d+)%s")
            if port then table.insert(r.network.local_ports, tonumber(port)) end
        end
    end

    -- Host/port probing
    if THOST and PORT then
        local tcp = require("tcp")
        local ok, client = pcall(function() return tcp.open(THOST .. ":" .. tostring(PORT)) end)
        if ok and client then
            r.probe_success = true
            r.probe_addr = THOST .. ":" .. tostring(PORT)
            pcall(function() client:close() end)
        else
            r.probe_success = false
            r.probe_error = tostring(client)
            r.probe_addr = THOST .. ":" .. tostring(PORT)
        end
    end

    -- File access
    if SAMPLE_FILE then
        local content = file_exists(SAMPLE_FILE)
        if content then
            r.file_exists = true
            r.file_size = #content
            local crypto = require("crypto")
            r.file_sha256 = crypto.sha256(content)
        else
            r.file_exists = false
        end
    end

    return r
end

return probe()