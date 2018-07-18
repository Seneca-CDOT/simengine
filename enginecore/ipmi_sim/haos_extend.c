/*
 * marvel_mod.c
 *
 * Marvell specific modules for handling BMC and MC functions.
 *
 * Author: MontaVista Software, Inc.
 *         Corey Minyard <minyard@mvista.com>
 *         source@mvista.com
 *
 */

#include <stdio.h>
#include <stdlib.h>
#include <errno.h>
#include <string.h>
#include <sys/time.h>
#include <sys/ioctl.h>
#include <unistd.h>
#include <signal.h>
#include <pthread.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <semaphore.h>

#include <OpenIPMI/ipmi_msgbits.h>
#include <OpenIPMI/ipmi_bits.h>
#include <OpenIPMI/serv.h>
// #include <hiredis/hiredis.h>

#define PVERSION "0.0.0"

#define NUM_BOARDS 1

#define CHASSIS_FRU_SIZE 1024
#define BOARD_FRU_SIZE 2048

#define BOARD_TEMP_SHUTDOWN 105
#define SWITCH_TEMP_SHUTDOWN 115
#define FRONT_TEMP_SHUTDOWN 50

#define MARVELL_SEMI_ISREAL_IANA	20495
#define DISABLE_NETWORK_SRVC_CMD	1
#define RELOAD_BOARD_FRU_CMD		2
#define SET_ALL_FANS_DUTY_CMD		3
#define GET_ALL_FANS_DUTY_CMD		4

#define BOARD_FRU_FILE "/etc/ipmi/axp_board_fru"
#define COLD_POWER_FILE "/var/lib/ipmi_sim_coldpower"
#define RESET_REASON_FILE "/var/lib/reset_reason"
#define RESET_REASON_UNKNOWN 0
#define RESET_REASON_COLD_BOOT 1
#define RESET_REASON_WARM_BOOT 2


static lmc_data_t *bmc_mc;
static unsigned int server_id = 0;
// redisContext *redis_store;

static struct board_info {
    sys_data_t *sys;

    lmc_data_t *mc;
    unsigned char num;
    char present;
    char fru_good;
    unsigned char fru[BOARD_FRU_SIZE];
    struct timeval button_press_time;
    unsigned int power_off_countdown;
    char button_pressed;
    char waiting_power_off;

    volatile char fru_data_ready_for_handling;

    /*
     * Tracks the state of the power request line, request happens
     * on a 1->0 transition.
     */
    char last_power_request;
} boards[NUM_BOARDS];


int ipmi_sim_module_print_version(sys_data_t *sys, char *options) {
  printf("IPMI Simulator module version %s\n", PVERSION);
  return 0;
}

static int say_hello(emu_out_t  *out,
				   emu_data_t *emu,
				   lmc_data_t *mc,
				   char       **toks) {
    out->printf(out, "Hi there \n");
    return EINVAL;
        
}

static int
bmc_set_chassis_control(lmc_data_t *mc, int op, unsigned char *val,
			void *cb_data)
{
  sys_data_t *sys = cb_data;
  char power_cmd[100] = {0};
  unsigned int i;

  switch (op) {
    case CHASSIS_CONTROL_POWER:
    case CHASSIS_CONTROL_RESET:
    case CHASSIS_CONTROL_BOOT_INFO_ACK:
    case CHASSIS_CONTROL_BOOT:
    case CHASSIS_CONTROL_GRACEFUL_SHUTDOWN:
	  break;
    default:
	  return EINVAL;
  }

	struct timeval now;
	sys->get_real_time(sys, &now);
	sys->log(sys, DEBUG, NULL, "Power request for all boards,"
		 " val=%d, now=%ld.%ld, asset=%d, op=%d",
		 *val, now.tv_sec, now.tv_sec, server_id, op);
  
  if (*val == 0 || op == CHASSIS_CONTROL_GRACEFUL_SHUTDOWN) {
    char* hard_flag = "--hard";
    if (op == CHASSIS_CONTROL_GRACEFUL_SHUTDOWN) {
      hard_flag = "";
    }
    sprintf(power_cmd, "simengine-cli.py power down --asset-key=%d %s", server_id, hard_flag);
    sys->log(sys, DEBUG, NULL, power_cmd);
    system(power_cmd);
  } else if (*val == 1) {
    sprintf(power_cmd, "simengine-cli.py power up --asset-key=%d", server_id);
    system(power_cmd);
  }

  return 0;
}

static int
bmc_get_chassis_control(lmc_data_t *mc, int op, unsigned char *val,
			void *cb_data)
{
  sys_data_t *sys = cb_data;
  sys->log(sys, DEBUG, NULL, "GETTING STATUS PALS!! %d", val);
  return 0;
}


/**************************************************************************
 * Module initialization
 *************************************************************************/
int ipmi_sim_module_init(sys_data_t *sys, const char *options) {
  
  int rv;
  char *initstr = strdup(options);
  const char *c;
  char *next;
  c = mystrtok(initstr, " \t\n", &next);
  server_id = 9191;
  
  while (c) {
    if (strncmp(c, "asset_id=", 9) == 0) {
      server_id = strtoul(c + 9, NULL, 0);
    }

    c = mystrtok(NULL, " \t\n", &next);
  }

  free(initstr);

  // redis_store = redisConnect("localhost", 6379);
  // if (redis_store != NULL && redis_store->err) {
  //   sys->log(sys, OS_ERROR, NULL,"Unable to connect to redis: %s", redis_store->errstr);
  //   return 0;
  // } else {
  //    sys->log(sys, DEBUG, NULL, "Connected to Redis\n");
  // }

  ipmi_emu_add_cmd("say_hello", NOMC, say_hello);
  rv = ipmi_mc_alloc_unconfigured(sys, 0x20, &bmc_mc);

  if (rv) {
	  sys->log(sys, OS_ERROR, NULL,"Unable to allocate an mc: %s", strerror(rv));
	  return rv;
  }

  // power control
  ipmi_mc_set_chassis_control_func(bmc_mc, bmc_set_chassis_control, NULL, sys);


  return 0;
}



