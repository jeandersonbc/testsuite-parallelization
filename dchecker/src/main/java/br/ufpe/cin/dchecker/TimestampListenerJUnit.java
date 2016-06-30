package br.ufpe.cin.dchecker;

import java.rmi.dgc.VMID;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;
import java.util.logging.Level;
import java.util.logging.Logger;

import org.junit.runner.Description;
import org.junit.runner.Result;
import org.junit.runner.notification.Failure;
import org.junit.runner.notification.RunListener;

import br.ufpe.cin.dchecker.model.TestRunInfo;
import br.ufpe.cin.dchecker.model.Verdict;

/**
 * An auxiliary listener for JUnit.<br>
 * Logs a given test name, when it started, when it finished, thread and and if
 * it has failed or passed.
 *
 * @author Jeanderson Candido -
 *         <a href="http://jeandersonbc.github.io">http://jeandersonbc.github.io
 *         </a>
 *
 */
public class TimestampListenerJUnit extends RunListener {

	private Map<String, Long> started;
	private Map<String, Long> finished;
	private Map<String, String> thread;
	private Set<String> ignored;
	private String hostVm;

	@Override
	public void testRunStarted(Description description) throws Exception {
		started = new HashMap<>();
		finished = new HashMap<>();
		ignored = new HashSet<>();
		thread = new HashMap<>();
		String vmid = (new VMID()).toString();

		// Ignoring last field which is a UUID
		hostVm = vmid.substring(0, vmid.lastIndexOf(":"));
		super.testRunStarted(description);
	}

	@Override
	public void testStarted(Description description) throws Exception {
		started.put(description.getDisplayName(), System.currentTimeMillis());
		thread.put(description.getDisplayName(), Thread.currentThread().getName());
		super.testStarted(description);
	}

	@Override
	public void testFinished(Description description) throws Exception {
		finished.put(description.getDisplayName(), System.currentTimeMillis());
		super.testFinished(description);
	}

	@Override
	public void testIgnored(Description description) throws Exception {
		ignored.add(description.getDisplayName());
		super.testIgnored(description);
	}

	@Override
	public void testRunFinished(Result result) throws Exception {
		Logger logger = Logger.getLogger(getClass().getName());
		logger.setLevel(Level.INFO);

		Set<String> failedTests = getFailedTestsFrom(result);

		for (Map.Entry<String, Long> test : started.entrySet()) {
			String testName = test.getKey();

			// At the following point, tests can be either FAILED or PASSED.
			// Ignored tests should not be considered.
			if (!this.ignored.contains(testName)) {
				StringBuilder sb = new StringBuilder("[DCHECKER]");

				TestRunInfo runningInfo = new TestRunInfo();
				runningInfo.setEnd(finished.get(testName));
				runningInfo.setHost(hostVm);
				runningInfo.setName(testName);
				runningInfo.setResult(failedTests.contains(testName) ? Verdict.FAIL : Verdict.PASS);
				runningInfo.setStart(started.get(testName));
				runningInfo.setThread(thread.get(testName));

				sb.append(runningInfo.toString());
				logger.info(sb.toString());
			}
		}
		super.testRunFinished(result);

	}

	private Set<String> getFailedTestsFrom(Result result) {
		Set<String> failedTests = new HashSet<>();
		for (Failure f : result.getFailures()) {
			Description description = f.getDescription();
			if (description.isTest()) {
				failedTests.add(description.getDisplayName());
			}
		}
		return failedTests;
	}
}
