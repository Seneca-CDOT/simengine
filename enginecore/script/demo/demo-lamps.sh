# Turn/off random PDU outlets

SIM_PDU_ADDR="192.168.124.5"
APC_PDU_ADDR="192.168.124.6"
OUT_OID="1.3.6.1.4.1.318.1.1.12.3.3.1.1.4"
OID_ONLINE_VAL=1
OID_OFFLINE_VAL=2

lamp_socket[0]=2
lamp_socket[1]=4
lamp_socket[2]=8

# set all on
for i in $(seq 1 8); do
        eval "snmpset -c public -v 1 $SIM_PDU_ADDR $OUT_OID.$i i $OID_ONLINE_VAL";
        eval "snmpset -c private -v 1 $APC_PDU_ADDR $OUT_OID.$i i $OID_ONLINE_VAL";
        sleep 1;
done


# do random actions
while true
do
        # get current outlet oid value
        rand_num=$[ $RANDOM % 3 ]
        out_num=${lamp_socket[$rand_num]}
        oid_state=$(eval snmpget -c public -Ov -v 1 $SIM_PDU_ADDR "$OUT_OID.$out_num")
        old_status="${oid_state//[!0-9]/}"
        # determine new value
        if [[ $old_status -ne $OID_ONLINE_VAL ]]; then
	  status=$OID_ONLINE_VAL
        else
	  status=$OID_OFFLINE_VAL
        fi
	
	# update OID status
       	eval "snmpset -c public -v 1 $SIM_PDU_ADDR $OUT_OID.$out_num i $status";
        # eval "snmpset -c private -v 1 $APC_PDU_ADDR $OUT_OID.$out_num i $status";
        sleep 3
done
