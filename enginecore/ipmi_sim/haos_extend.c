/*
 * haos_extend.c
 *
 * Simengine extended chassis control
 *
 * Author: OSTEP Team, CDOT
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

#define PVERSION "0.0.0"

#define NUM_BOARDS 1

#define CHASSIS_FRU_SIZE 1024
#define BOARD_FRU_SIZE 2048

static lmc_data_t *bmc_mc;
static unsigned int server_id = 0;

static struct board_info
{
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

int ipmi_sim_module_print_version(sys_data_t *sys, char *options)
{
  printf("IPMI Simulator module version %s\n", PVERSION);
  return 0;
}

static int
bmc_get_chassis_control(lmc_data_t *mc, int op, unsigned char *val,
                        void *cb_data)
{
  sys_data_t *sys = cb_data;
  char power_cmd[100] = {0};

  sprintf(power_cmd, "simengine-cli status --value --asset-key=%d", server_id);

  // execute a command
  FILE *fp = popen(power_cmd, "r");
  if (fp == NULL)
  {
    sys->log(sys, OS_ERROR, NULL, "Failed to fetch asset status; CAUSE: %s", strerror(errno));
    // according to the popen docs, the only time it would return NULL is when
    // 1) `fork` call fails
    // 2) `pipe` call fails
    // 3) unable to allocated memory
    // therefore, this is likely a severe error; stop the simulator
    exit(1);
  }
  else
  {
    // get the command result
    char result[24] = {0x0};
    while (fgets(result, sizeof(result), fp) != NULL)
    {
      *val = atoi(result);
    }

    if (pclose(fp) < 0)
    {
      sys->log(sys, OS_ERROR, NULL, "Failed to close file handle; CAUSE: %s", strerror(errno));
      // failing to clean up is most likely a severe error; stop the simulator
      exit(1);
    }
  }

  return 0;
}

static int
bmc_set_chassis_control(lmc_data_t *mc, int op, unsigned char *val,
                        void *cb_data)
{
  sys_data_t *sys = cb_data;
  char power_cmd[100] = {0};
  unsigned int i;

  switch (op)
  {
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

  if (*val == 0 || op == CHASSIS_CONTROL_GRACEFUL_SHUTDOWN)
  {
    char *hard_flag = "--hard";
    if (op == CHASSIS_CONTROL_GRACEFUL_SHUTDOWN)
    {
      hard_flag = "";
    }
    sprintf(power_cmd, "simengine-cli power down --asset-key=%d %s", server_id, hard_flag);
    sys->log(sys, DEBUG, NULL, power_cmd);
    system(power_cmd);
  }
  else if (*val == 1)
  {
    sprintf(power_cmd, "simengine-cli power up --asset-key=%d", server_id);
    system(power_cmd);
  }

  return 0;
}

/**************************************************************************
 * Module initialization
 *************************************************************************/
int ipmi_sim_module_init(sys_data_t *sys, const char *options)
{

  int rv;
  char *initstr = strdup(options);
  const char *c;
  char *next;
  c = mystrtok(initstr, " \t\n", &next);
  server_id = 9191;

  while (c)
  {
    if (strncmp(c, "asset_id=", 9) == 0)
    {
      server_id = strtoul(c + 9, NULL, 0);
    }

    c = mystrtok(NULL, " \t\n", &next);
  }

  free(initstr);

  rv = ipmi_mc_alloc_unconfigured(sys, 0x20, &bmc_mc);

  if (rv)
  {
    sys->log(sys, OS_ERROR, NULL, "Unable to allocate an mc: %s", strerror(rv));
    return rv;
  }

  // power control
  ipmi_mc_set_chassis_control_func(bmc_mc, bmc_set_chassis_control, bmc_get_chassis_control, sys);

  return 0;
}
