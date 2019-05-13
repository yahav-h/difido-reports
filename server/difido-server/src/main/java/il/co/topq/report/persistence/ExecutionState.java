package il.co.topq.report.persistence;

import javax.persistence.Entity;
import javax.persistence.Id;

import org.springframework.cache.annotation.Cacheable;

@Entity
@Cacheable
public class ExecutionState {
	
	@Id
	private int id;
	
	/**
	 * Is the execution is currently active or is it already finished
	 */
	private boolean active;

	/**
	 * If execution is locked it will not be deleted from disk no matter how old
	 * it is
	 */
	private boolean locked;
	
	/**
	 * When the HTML is deleted, the flag is set to false. This can happen if
	 * the execution age is larger then the maximum days allowed.
	 */
	private boolean htmlExists;

	
	public int getId() {
		return id;
	}

	public void setId(int id) {
		this.id = id;
	}

	public boolean isActive() {
		return active;
	}

	public void setActive(boolean active) {
		this.active = active;
	}

	public boolean isLocked() {
		return locked;
	}

	public void setLocked(boolean locked) {
		this.locked = locked;
	}

	public boolean isHtmlExists() {
		return htmlExists;
	}

	public void setHtmlExists(boolean htmlExists) {
		this.htmlExists = htmlExists;
	}

	
	
	
}