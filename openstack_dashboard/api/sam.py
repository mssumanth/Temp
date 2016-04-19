vpn='vpn'
if vpn:
    print "Helloi"
    addresses = {"public":"172.0.0.0"}
    for key, val in addresses.iteritems():
        print "KEY:",key
        print "VAL:",val
