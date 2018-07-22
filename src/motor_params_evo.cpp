/* * * * * * * * * * * * * * * * * * *
 * Matthias Kubisch                  *
 * kubisch@informatik.hu-berlin.de   *
 * June 2018                         *
 * * * * * * * * * * * * * * * * * * */

#include "./motor_params_evo.h"

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
Evaluation::prepare_generation(unsigned /*cur_generation*/, unsigned /*max_generation*/) { return; }

void Evaluation::draw(void) const
{
    axis_ux.draw();
    plot_position.draw();
    plot_voltage .draw();
    plot_targ_pos.draw();
}

void
Evaluation::logdata(uint32_t cycles, uint32_t preparation_cycles = 0)
{
    /* drawing */
    auto const& j = robot.get_joints()[0];

    plot_position.add_sample(j.s_ang);
    plot_voltage .add_sample(j.motor.get());
    plot_targ_pos.add_sample(profile.get_position());

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
    assert(rand_value <= 1.0 and rand_value >= 0.0);

    unsigned steps = 0;
    unsigned max_steps = profile.get_length();

    profile.reset();
    robot.update();

    plot_position.reset();
    plot_voltage .reset();
    plot_targ_pos.reset();

    sts_msg("genome size:%u", genome.size());

    control.set_model_parameter(genome);
    fitness_function.start();

    while (steps < max_steps)
    {
        /* if evolution has been paused or aborted */
        if (do_quit.status()) return false; // abort
        else if (do_pause.status()) {
            usleep(10000); // 10 ms
            robot.idle();
            printf("halted\r");
            continue;
        }

        profile.step();
        control.execute_cycle();

        if (!robot.update())
        {
            sts_msg("Evaluation got no response from Simloid. Sending quit signal.");
            quit();
            return false; // abort
        }

        if (not fitness_function.step())
            break;
        logdata(steps);
        ++steps;
    }

    fitness_function.finish();

    robot.restore_state();
    fitness.set_value(fitness_function.get_value());
    return true;
}


bool
Evaluation::test_mode_step(std::vector<double> genome)
{
    unsigned steps = 0;
    unsigned max_steps = profile.get_length();


    MidiParams mp(midi, genome);
    mp.step();

    profile.reset();
    robot.update();

    //plot_position.reset();
    //plot_voltage .reset();
    //plot_targ_pos.reset();

    control.set_model_parameter(genome);

    while (steps < max_steps)
    {
        usleep(1000);
        mp.step();
        /* if paused or aborted */
        if (do_quit.status()) return false; // abort
        else if (do_pause.status()) {
            usleep(10000); // 10 ms
            robot.idle();
            printf("halted\r");
            continue;
        }

        profile.step();
        control.execute_cycle();

        if (!robot.update())
        {
            sts_msg("Testmode got no response from Simloid. Sending quit signal.");
            quit();
            return false; // abort
        }

        logdata(steps);
        ++steps;
    }

    robot.restore_state();
    return true;
}

bool
Application::loop(void)
{
    if (test_mode) {
        evaluation.test_mode_step( evolution->get_best_individuals_genome());
        return true;
    }

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

void
Application::user_callback_key_pressed(const SDL_Keysym& keysym)
{
    switch (keysym.sym)
    {
        /* for all motors */
        case SDLK_t:
            test_mode = !test_mode;
            sts_msg("TESTMODE: %s", (test_mode)? "ON":"OFF");
            break;
        default:
            break;
    }
}


APPLICATION_MAIN()
