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
}

void
Evaluation::prepare(void)
{
    /*TODO:
        reset the robot
        set new random position
        save state
    */
    return;
}

void Evaluation::draw(void) const
{
    axis_position_xy.draw();
    plot_position_xy.draw();

    axis_position_z.draw();
    plot_position_z.draw();
    plot_rotation_z.draw();
}

void
Evaluation::logdata(uint32_t cycles, uint32_t preparation_cycles = 0)
{
    /* drawing */
    plot_position_xy.add_sample(robot.get_avg_position().x,
                                robot.get_avg_position().y);

    plot_position_z.add_sample(robot.get_avg_position().z);
    plot_rotation_z.add_sample(robot.get_avg_rotation()/M_PI);

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
    fitness_data data;
    /* 10% of initial steps is random time, equal for each individual of a certain generation*/
    const unsigned int rnd_steps = (unsigned int) (0.1 * rand_value * settings.initial_steps);
    Vector3 push_force(0.0);
    const bool push_on = (settings.push_cycle > 0 and
                          settings.push_steps > 0 and
                          settings.push_strength > .0);

    unsigned int body_index = 0;
    control.reset();
    robot.update();

    plot_position_xy.reset();
    plot_position_z .reset();
    plot_rotation_z .reset();

    if (settings.initial_steps > 0) // trial begins with seed, then switches to evolving parameters
    {
        uint64_t max_initial_steps = settings.initial_steps + rnd_steps;
        control.set_control_parameter(param0); // load seed controller
        if (verbose) dbg_msg(" %u initial + %u random steps" , settings.initial_steps, rnd_steps); // TODO remove

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

        } // end while

        data.steps = 0; // reset time

    } // end if seed

    control.set_control_parameter(genome); // apply new controller weights
    fitness_function->start(data);

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

        // TODO make the pushes have all same AUC (area under curve) smaller pushes have longer duration
        if (push_on)
        {
            if (settings.push_mode == 0) { // random pushes
                if (data.steps % settings.push_cycle == 0)
                {
                    push_force.random(-settings.push_strength, settings.push_strength);
                    body_index = random_index(robot.get_number_of_bodies());
                    robot.set_force(body_index, push_force);
                }
                else if (data.steps % settings.push_cycle == settings.push_steps)
                {
                    push_force.zero();
                    robot.set_force(body_index, push_force); // set force to zero
                }
            } else {
                if (data.steps == settings.push_cycle)
                {
                    push_force.x = settings.push_strength;
                    robot.set_force(settings.push_body, push_force);
                } else if (data.steps == settings.push_cycle + settings.push_steps) {
                    push_force.zero();
                    robot.set_force(settings.push_body, push_force);
                }
            }
        }
        data.power += control.get_normalized_mechanical_power();

        if (!robot.update())
        {
            sts_msg("Evaluation got no response from Simloid. Sending quit signal.");
            quit();
            return false; // abort
        }

        fitness_function->step(data);
        logdata(data.steps);
        ++data.steps;

        /* drop penalty */
        if (data.dropped or data.out_of_track or data.stopped)
        {
            if (verbose) sts_msg(" %04d/%04d %s%s%s", data.steps, settings.max_steps
                                                    , data.dropped      ? "[Dropped]"      : ""
                                                    , data.out_of_track ? "[Out of track]" : ""
                                                    , data.stopped      ? "[Stopped]"      : "" );
            break;
        }

        /* evolve efficient motion? */
        if (settings.efficient && (data.power >= settings.max_power))
        {
            if (verbose) sts_msg(" %04d/%04d Power exceeded.", data.steps, settings.max_steps);
            break;
        }

        if (data.steps >= settings.max_steps)
        {
            if (verbose) sts_msg(" %04d/%04d Time's up.", data.steps, settings.max_steps);
        }
    }

    fitness_function->finish(data);

    robot.restore_state();
    fitness.set_value(data.fit);
    return true; // all OK, continue with next
}

bool
Application::loop(void)
{
    if (evolution->get_current_trial() % evolution->get_population_size() == 0)
    {
        const statistics_t& fstats = evolution->get_fitness_statistics();
        plot1D_max_fitness.add_sample(fstats.max);
        plot1D_avg_fitness.add_sample(fstats.avg);
        plot1D_min_fitness.add_sample(fstats.min);

        const statistics_t& mstats = evolution->get_mutation_statistics();
        plot1D_max_mutation.add_sample(mstats.max);
        plot1D_avg_mutation.add_sample(mstats.avg);
        plot1D_min_mutation.add_sample(mstats.min);
    }
    return evolution->loop();
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
