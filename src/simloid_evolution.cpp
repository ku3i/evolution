/*
 * Matthias Kubisch
 * kubisch@informatik.hu-berlin.de
 */

#include "./simloid_evolution.h"

/* framework */
#include <common/modules.h>
#include <common/setup.h>

DEFINE_GLOBALS()

void
Application::draw(const pref& /*p*/) const
{
    axis_fitness.draw();
    plot1D_min_fitness.draw();
    plot1D_avg_fitness.draw();
    plot1D_max_fitness.draw();
    axis_mutation.draw();
    plot1D_min_mutation.draw();
    plot1D_avg_mutation.draw();
    plot1D_max_mutation.draw();

    evaluation.draw();

    glprintf(-.99,-.90,0.0, 0.04, "Trial: %lu/%lu" , evolution->get_current_trial(), evolution->get_number_of_trials());

}

void Evaluation::prepare_generation(unsigned cur_generation, unsigned max_generation)
{
    prepare_evaluation(cur_generation*settings.population_size, max_generation*settings.population_size);
}

void
Evaluation::prepare_evaluation(unsigned cur_trial, unsigned max_trial)
{

    growth = clip(settings.growth.init + cur_trial*settings.growth.rate, 0.0, 1.0);

    if ("NONE" == settings.rnd.mode or settings.rnd.mode.empty()) {
        /* do nothing */
        if (0 == cur_trial and growth == 1.0) return;
        sts_msg("Preparing new model (growing only).");
        rnd_amp = 0.0;
        robot.randomize_model(rnd_amp, growth, settings.friction, /*inst=*/0); // only for initial position, TODO this could be removed if initial position is defined by client
    }
    else if ("LIN_INC" == settings.rnd.mode)
    {
        rnd_amp = (double) cur_trial / max_trial;
        sts_msg("Preparing new randomized model with linearly increasing amplitude %lf in trial %u of %u", rnd_amp, cur_trial, max_trial);
        robot.randomize_model(rnd_amp, growth, settings.friction, /*inst=*/0);
    }
    else if ("CONSTANT" == settings.rnd.mode) {
        rnd_amp = settings.rnd.value;
        sts_msg("Preparing new randomized model with constant amplitude %lf.", rnd_amp);
        if (0 != settings.rnd.init)
            sts_msg("Using random initial seed: %lu", settings.rnd.init);
        robot.randomize_model(rnd_amp, growth, settings.friction, settings.rnd.init);
    }
    else if ("CONSTANT_ONCE" == settings.rnd.mode) {
        rnd_amp = settings.rnd.value;
        sts_msg("Preparing new randomized model with constant amplitude %lf.", rnd_amp);
        if (0 == settings.rnd.init) {
            sts_msg("Using random initial seed: %lu", settings.rnd.init);
            settings.rnd.init = robot.randomize_model(rnd_amp, growth, settings.friction, settings.rnd.init); /* returns random seed */
        } else {
            robot.randomize_model(rnd_amp, growth, settings.friction, settings.rnd.init);
        }
    }
    else err_msg(__FILE__,__LINE__,"Unrecognized random mode setting: '%s'.", settings.rnd.mode.c_str());

    return;
}

void Evaluation::draw(void) const
{
    axis_position_xy.draw();
    plot_position_xy.draw();

    axis_position_z.draw();
    plot_position_z.draw();
    plot_rotation_z.draw();
    plot_velocity_y.draw();

    glColor3f(1.0,1.0,1.0);
    glprintf(-.99,-.60,0.0, 0.04, "py: %5.2f px: %5.2f" , robot.get_avg_position().y, robot.get_avg_position().x);
    glprintf(-.99,-.65,0.0, 0.04, "power: %5.2f/%lu", data.power, settings.max_power);
    glprintf(-.99,-.70,0.0, 0.04, "steps: %5lu/%lu" , data.steps, settings.max_steps);
    glprintf(-.99,-.75,0.0, 0.04, "random: %5.2f pa", rnd_amp*100);
    glprintf(-.99,-.80,0.0, 0.04, "growth: %5.2f pa", growth*100);
    glprints(-.99,-.85,0.0, 0.04, settings.project_name);
}

void
Evaluation::logdata(uint32_t cycles, uint32_t preparation_cycles = 0)
{
    /* drawing */
    plot_position_xy.add_sample(robot.get_avg_position().x,
                                robot.get_avg_position().y);

    plot_position_z.add_sample(robot.get_avg_position().z);
    plot_rotation_z.add_sample(robot.get_avg_rotation()/M_PI);
    plot_velocity_y.add_sample(robot.get_avg_velocity_forward());

    if (logger.is_enabled())
        logger.log("%lld %s"// use %+e
                  , static_cast<int64_t>(cycles - preparation_cycles)
                  , robot_log.log()
                  );

    if (logger.is_video_included())
        robot.record_next_frame();
}

bool
Evaluation::evaluate(Fitness_Value &fitness, const std::vector<double>& genome, double rand_value)
{
    assert(fitness_function != nullptr);
    data = fitness_data{};

    /* 10% of initial steps is random time, equal for each individual of a certain generation*/
    const unsigned int rnd_steps = (unsigned int) (0.1 * rand_value * settings.initial_steps);
    Vector3 push_force(0.0);
    const bool push_on = (settings.push.cycle > 0 and
                          settings.push.steps > 0 and
                          settings.push.strength > .0);

    unsigned int body_index = 0;
    control.reset();
    robot.update();

    plot_position_xy.reset();
    //plot_position_z .reset();
    //plot_rotation_z .reset();
    //plot_velocity_y .reset();

    if (settings.initial_steps > 0) // trial begins with seed, then switches to evolving parameters
    {
        uint64_t max_initial_steps = settings.initial_steps + rnd_steps;
        control.set_control_parameter(param0); // load seed controller

        while (data.steps < max_initial_steps) // wait
        {
            if (do_quit.status()) return false; // abort
            else if (do_pause.status()) {
                usleep(10000); // 10 ms
                robot.idle();
                printf("halted\r");
                continue;
            }

            control.execute_cycle();
            if (!robot.update())
            {
                sts_msg("Evaluation gets no response from Simloid. Sending quit signal.");
                quit();
                return false; // abort
            }

            logdata(data.steps, max_initial_steps);
            ++data.steps;
            ++cycles;

        } // end while

        data.steps = 0; // reset time

    } // end if seed

    control.set_control_parameter(genome); // apply new controller weights
    fitness_function->start(data);
    data.max_steps = settings.max_steps;

    while (data.steps < settings.max_steps)
    {
        /* if evolution has been paused or aborted */
        if (do_quit.status()) return false; // abort
        else if (do_pause.status()) {
            usleep(10000); // 10 ms
            robot.idle();
            printf("halted\r");
            continue;
        }

        control.execute_cycle();

        /* IDEA: consider making nudges that have all same AUC (area under curve)
           i.a. smaller pushes have longer duration */

        if (push_on)
        {
            switch (settings.push.mode)
            {
            case 0: /*RANDOM BODY, RANDOM FORCE */
                if (data.steps % settings.push.cycle == 0)
                {
                    push_force.random(-settings.push.strength, settings.push.strength);
                    body_index = random_index(robot.get_number_of_bodies());
                    robot.set_force(body_index, push_force);
                }
                else if (data.steps % settings.push.cycle == settings.push.steps)
                {
                    push_force.zero();
                    robot.set_force(body_index, push_force); // set force to zero
                }
                break;

            case 1: /* SPECIFIC BODY, SPECIFIC FORCE, X-DIRECTION */
                if (data.steps == settings.push.cycle)
                {
                    push_force.x = settings.push.strength;
                    robot.set_force(settings.push.body, push_force);
                } else if (data.steps == settings.push.cycle + settings.push.steps) {
                    push_force.zero();
                    robot.set_force(settings.push.body, push_force);
                }
                break;

            case 2: /* SPECIFIC JOINT, INSERT MOTOR COMMAND */
                if (data.steps <= settings.push.steps)
                    control.insert_motor_command(settings.push.body,settings.push.strength);
                break;

            case 3: /* RANDOM BODY, INCREASING WITH TIME */
                if (data.steps % settings.push.cycle == 0)
                {
                    double a = clip(static_cast<double> (data.steps) / settings.max_steps, 0.0, 1.0);
                    push_force.random(-settings.push.strength*a, settings.push.strength*a);
                    body_index = random_index(robot.get_number_of_bodies());
                    robot.set_force(body_index, push_force);
                }
                else if (data.steps % settings.push.cycle == settings.push.steps)
                {
                    push_force.zero();
                    robot.set_force(body_index, push_force); // set force to zero
                }
                break;
            }
        }
        data.power += control.get_normalized_mechanical_power();
        data.dctrl += control.get_normalized_control_change();

        if (!robot.update())
        {
            sts_msg("Evaluation got no response from Simloid. Sending quit signal.");
            quit();
            return false; // abort
        }

        fitness_function->step(data);
        logdata(data.steps);
        ++data.steps;
        ++cycles;

        /* drop penalty */
        if (data.dropped or data.out_of_track or data.stopped)
        {
            if (verbose) sts_add("%04d/%04d %s%s%s", data.steps, settings.max_steps
                                                   , data.dropped      ? "[Dropped]" : ""
                                                   , data.out_of_track ? "[Outside]" : ""
                                                   , data.stopped      ? "[Stopped]" : "" );
            break;
        }

        /* evolve efficient motion? */
        if (settings.efficient && (data.power >= settings.max_power))
        {
            if (verbose) sts_add("%04d/%04d [PowerEx]", data.steps, settings.max_steps);
            break;
        }

        /* evolve jerk reduced motion? */
        if (settings.efficient && (data.dctrl >= settings.max_dctrl))
        {
            if (verbose) sts_add("%04d/%04d [DCtrlEx]", data.steps, settings.max_steps);
            break;
        }

        if (data.steps >= settings.max_steps)
        {
            if (verbose) sts_add("%04d/%04d [TimeOut]", data.steps, settings.max_steps);
        }
    }

    fitness_function->finish(data);

    //dbg_msg("L1=%1.3f #=%u(%u)", control.get_L1_norm(), control.get_number_of_symmetric_parameter(), control.get_number_of_parameter());

    robot.restore_state();
    fitness.set_value(data.fit);
    return true; // all OK, continue with next
}

bool
Application::loop(void)
{
    bool result = evolution->loop();
    if (evolution->get_current_trial() % evolution->get_population_size() == 0)
    {
        const statistics_t& fstats = evolution->get_fitness_statistics();
        if (fstats.num_samples>0) {
            plot1D_max_fitness.add_sample(fstats.max);
            plot1D_avg_fitness.add_sample(fstats.avg);
            plot1D_min_fitness.add_sample(fstats.min);
        }

        const statistics_t& mstats = evolution->get_mutation_statistics();
        if (mstats.num_samples>0) {
            plot1D_max_mutation.add_sample(mstats.max);
            plot1D_avg_mutation.add_sample(mstats.avg);
            plot1D_min_mutation.add_sample(mstats.min);
        }
    }
    return result;
}

void
Application::finish(void)
{
    evolution->finish();
    robot.finish();
    sts_msg("Finished shutting down all subsystems.");
    quit();
}

APPLICATION_MAIN()
