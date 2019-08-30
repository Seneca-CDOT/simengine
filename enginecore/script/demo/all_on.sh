# Turn all PDU outlets on
SIM_PDU_ADDR="localhost:1025"
APC_PDU_ADDR="10.42.1.94"
OUT_OID="1.3.6.1.4.1.318.1.1.12.3.3.1.1.4"
OID_ONLINE_VAL=1
OID_OFFLINE_VAL=2

lamp_socket[0]=2
lamp_socket[1]=5
lamp_socket[2]=8

# set all on
for i in $(seq 1 8); do
        eval "snmpset -c private -v 1 $APC_PDU_ADDR $OUT_OID.$i i $OID_ONLINE_VAL";
        sleep 1;
done


